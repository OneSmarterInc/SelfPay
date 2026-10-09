-- DRAFT: execute only after copy testing and Vikram approval of this file's commit.
BEGIN;
DELETE FROM preferences
WHERE tenant = 'guest'
  AND member_id IN (SELECT id FROM members WHERE tenant = 'guest');
COMMIT;
