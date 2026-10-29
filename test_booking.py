import datetime as dt
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import booking
import core

class BookingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/'test.sqlite'
        core.initialize(self.db)
        with core.connect(self.db) as db:db.executescript(booking.SCHEMA)
        self.env=patch.dict(os.environ,{'BOOKING_ENABLED':'true','SMTP_HOST':'mail.example.test','SMTP_USER':'test','SMTP_PASSWORD':'test','BOOKING_FROM_EMAIL':'sender@example.test','BOOKING_AUTH_SECRET':'x'*32,'BOOKING_CONTACTS_JSON':json.dumps({'center':{'email':'appointments@example.test','purpose':'appointment_requests','evidence_url':'https://example.test/contact'}})})
        self.env.start();self.addCleanup(self.env.stop)
        self.mail=patch.object(booking,'send_email');self.send=self.mail.start();self.addCleanup(self.mail.stop)
        self.entry={'name':'Synthetic center','email':'appointments@example.test','coverage':'Synthetic address'}
        with core.connect(self.db) as db:
            db.execute('INSERT INTO batches VALUES(?,?,?,?,?,?)',('test','hash','test',0,'published','{}'))
            db.execute('INSERT INTO entries VALUES(?,?,?,?)',('test','center','hash',json.dumps(self.entry)))
            db.execute('INSERT INTO settings VALUES(?,?)',('active_batch','test'))

    def account(self):
        r=booking.start_account(dict(name='Test User',email='user@example.test',consent=True),self.db)
        code=re.search(r'\b\d{6}\b',self.send.call_args.args[2])[0]
        auth=booking.verify_account(dict(challenge_id=r['challenge_id'],code=code),self.db)
        return auth

    def form(self):
        return dict(request_id='3f94dab2-9ffa-47c3-bbec-e861e42e7531',entry_key='center',name='Test User',phone='555-555-0100',datetime=(dt.datetime.now()+dt.timedelta(days=3)).strftime('%Y-%m-%dT12:00'),timezone='America/New_York',service='MRI',consent=True)

    def test_disabled_and_unapproved_center_hide_action(self):
        self.assertEqual(booking.contact('center',self.entry),'appointments@example.test')
        self.assertIsNone(booking.contact('other',self.entry))
        self.assertIsNone(booking.contact('center',dict(self.entry,email=None)))
        with patch.dict(os.environ,{'BOOKING_ENABLED':'false'}):
            self.assertIsNone(booking.contact('center',self.entry))
            with self.assertRaises(booking.Unavailable):self.account()

    def test_verified_account_and_single_use_code(self):
        r=booking.start_account(dict(name='Test User',email='user@example.test',consent=True),self.db)
        code=re.search(r'\b\d{6}\b',self.send.call_args.args[2])[0]
        auth=booking.verify_account(dict(challenge_id=r['challenge_id'],code=code),self.db)
        self.assertEqual(core.session(auth['token'],self.db)['tenant'],'booking')
        with self.assertRaises(ValueError):booking.verify_account(dict(challenge_id=r['challenge_id'],code=code),self.db)

    def test_wrong_code_attempts_are_committed(self):
        r=booking.start_account(dict(name='Test User',email='user@example.test',consent=True),self.db)
        code=re.search(r'\b\d{6}\b',self.send.call_args.args[2])[0]
        wrong='111111' if code!='111111' else '222222'
        for _ in range(5):
            with self.assertRaises(ValueError):booking.verify_account(dict(challenge_id=r['challenge_id'],code=wrong),self.db)
        with self.assertRaises(ValueError):booking.verify_account(dict(challenge_id=r['challenge_id'],code=code),self.db)

    def test_guest_cannot_send(self):
        with self.assertRaises(PermissionError):booking.submit({'tenant':'guest'},self.form(),self.db)
        self.send.assert_not_called()

    def test_request_server_recipient_and_no_duplicate_send(self):
        member=self.account()['member'];self.send.reset_mock()
        data=self.form();data['email']='attacker@example.test'
        result=booking.submit(member,data,self.db)
        self.assertEqual(result['status'],'email_accepted')
        self.assertEqual(self.send.call_args.args[0],'appointments@example.test')
        self.assertIn('not a confirmed booking',self.send.call_args.args[2])
        self.assertEqual(booking.submit(member,data,self.db),result)
        self.assertEqual(self.send.call_count,1)

    def test_unknown_delivery_not_resent(self):
        member=self.account()['member'];self.send.reset_mock();self.send.side_effect=TimeoutError()
        data=self.form()
        self.assertEqual(booking.submit(member,data,self.db)['status'],'delivery_unknown')
        booking.submit(member,data,self.db)
        self.assertEqual(self.send.call_count,1)

    def test_validation_and_unapproved_destination(self):
        member=self.account()['member'];self.send.reset_mock()
        for delta in [dict(consent=False),dict(datetime='2000-01-01T12:00'),dict(timezone='Invalid/Zone'),dict(entry_key='absent'),dict(phone='x')]:
            with self.assertRaises(ValueError):booking.submit(member,dict(self.form(),**delta),self.db)
        with patch.dict(os.environ,{'BOOKING_CONTACTS_JSON':'{}'}):
            with self.assertRaises(ValueError):booking.submit(member,self.form(),self.db)
        self.send.assert_not_called()

if __name__=='__main__':unittest.main()
