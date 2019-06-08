import unittest

from yaboli import message

class TestMessage(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_message(self):
		m = message.Message({ # older message
			"edited": None,
			"deleted": None,
			"time": 1440104478,
			"id": "00q5kdu2xd4ao",
			"sender": {
				"id": "agent:pxXsVkA4L2s=",
				"name": "Garmy",
				"server_id": "heim.1",
				"server_era": "00q2lx69ur11c",
				"session_id": "70785873566b41344c32733d-e27e0a924311bc4f",
			},
			"content": "I claim this room!"
		})
		self.assertEqual(m.id(),                      "00q5kdu2xd4ao"      )
		self.assertEqual(m.parent(),                  None                 )
		self.assertEqual(m.content(),                 "I claim this room!" )
		self.assertEqual(m.sender().user_id(),        "agent:pxXsVkA4L2s=" )
		self.assertEqual(m.time(),                    1440104478           )
		self.assertEqual(m.time_formatted(),          "21:01:18"           )
		self.assertEqual(m.time_formatted(date=True), "2015-08-20 21:01:18")
		self.assertEqual(m.deleted(),                 False                )
		
		m = message.Message({ # newer message
			"edited": None,
			"deleted": None,
			"time": 1460836596,
			"id": "01dxs00kvhh4w",
			"parent": "01dxrya95iark",
			"sender": {
				"id": "account:010nrwbcafx8g",
				"name": "Xyzzy",
				"server_id": "heim.4",
				"server_era": "01cwcninm0feo",
				"session_id": "44514577654132456c746b3d-bcf7c88ae84daebd",
				"client_address": "9d13:4a20",
				"is_manager": True,
			},
			"content": "Hello."
		})
		self.assertEqual(m.id(),                      "01dxs00kvhh4w"        )
		self.assertEqual(m.parent(),                  "01dxrya95iark"        )
		self.assertEqual(m.content(),                 "Hello."               )
		self.assertEqual(m.sender().user_id(),        "account:010nrwbcafx8g")
		self.assertEqual(m.time(),                    1460836596             )
		self.assertEqual(m.time_formatted(),          "19:56:36"             )
		self.assertEqual(m.time_formatted(date=True), "2016-04-16 19:56:36"  )
		self.assertEqual(m.deleted(),                 False                  )

if __name__ == '__main__':
	unittest.main()
