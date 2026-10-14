-- DRAFT: execute only after owner approval, verified pre-write backup and branch-copy test/waiver.
-- IDs are from the October 12 snapshot; any scope mismatch aborts the transaction.
\set ON_ERROR_STOP on
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
LOCK TABLE public.members, public.conversations, public.preferences,
           public.corrections, public.sessions, public.guest_usage IN SHARE ROW EXCLUSIVE MODE;
CREATE TEMP TABLE cleanup_members(id text PRIMARY KEY) ON COMMIT DROP;
INSERT INTO cleanup_members VALUES
    ('f8f89ee1-66e7-4e42-a848-ca3d6e4f5c51'),
    ('12dca885-1548-43d2-b219-46d04095c26e'),
    ('24651e6b-7cf9-43b5-8b90-6a521679c6a7'),
    ('bcd03d50-9604-43a7-be0b-5f1ec5594794');
CREATE TEMP TABLE cleanup_conversations(id text PRIMARY KEY) ON COMMIT DROP;
INSERT INTO cleanup_conversations VALUES
    ('ae0db782-c14a-4058-a90d-1fc35f089808'),
    ('45dc013c-7da4-4912-8c3f-2a17baf3b210'),
    ('bff688e0-cc2c-40f4-98db-3b3fa9403d17'),
    ('3e703856-c363-4a12-980b-5109ef7f552a'),
    ('d7e2f4f2-3c65-497f-906a-6892e73a0325'),
    ('ff737275-12ff-4489-9411-72300492f6f2');
DO $$
BEGIN
    IF (SELECT count(*) FROM public.members WHERE tenant <> 'guest') <> 4
       OR (SELECT count(*) FROM public.members m JOIN cleanup_members t USING(id) WHERE m.tenant <> 'guest') <> 4 THEN
        RAISE EXCEPTION 'Member scope changed; stop and review';
    END IF;
    IF (SELECT count(*) FROM public.conversations) <> 6
       OR (SELECT count(*) FROM public.conversations c JOIN cleanup_conversations t USING(id) JOIN cleanup_members m ON m.id=c.member_id) <> 6 THEN
        RAISE EXCEPTION 'Conversation scope changed; stop and review';
    END IF;
    IF (SELECT count(*) FROM public.preferences p JOIN cleanup_members m ON m.id=p.member_id) <> 1
       OR NOT EXISTS (SELECT 1 FROM public.preferences WHERE member_id='f8f89ee1-66e7-4e42-a848-ca3d6e4f5c51' AND tenant='plan-a') THEN
        RAISE EXCEPTION 'Preference scope changed; stop and review';
    END IF;
    IF (SELECT count(*) FROM public.corrections c JOIN cleanup_members m ON m.id=c.member_id) <> 1
       OR NOT EXISTS (SELECT 1 FROM public.corrections WHERE id='cfb1605f7d3a9e0c6ab8e451' AND member_id='f8f89ee1-66e7-4e42-a848-ca3d6e4f5c51' AND tenant='plan-a') THEN
        RAISE EXCEPTION 'Correction scope changed; stop and review';
    END IF;
    IF EXISTS (SELECT 1 FROM public.sessions s JOIN cleanup_members m ON m.id=s.member_id)
       OR EXISTS (SELECT 1 FROM public.guest_usage g JOIN cleanup_members m ON m.id=g.member_id) THEN
        RAISE EXCEPTION 'Additional related data exists; stop and review';
    END IF;
END $$;
DELETE FROM public.conversations WHERE id IN (SELECT id FROM cleanup_conversations);
DELETE FROM public.preferences WHERE member_id='f8f89ee1-66e7-4e42-a848-ca3d6e4f5c51' AND tenant='plan-a';
DELETE FROM public.corrections WHERE id='cfb1605f7d3a9e0c6ab8e451' AND member_id='f8f89ee1-66e7-4e42-a848-ca3d6e4f5c51';
DELETE FROM public.members WHERE id IN (SELECT id FROM cleanup_members);
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM public.members WHERE tenant <> 'guest')
       OR EXISTS (SELECT 1 FROM public.conversations)
       OR EXISTS (SELECT 1 FROM public.corrections WHERE created >= extract(epoch FROM timestamptz '2026-10-13 00:00:00+05:30')) THEN
        RAISE EXCEPTION 'Synthetic backup guard still fails; transaction rolled back';
    END IF;
END $$;
COMMIT;
