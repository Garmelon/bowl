import unittest

from yaboli import session

class TestSession(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_session(self):
		s = session.Session({
			"id": "bot:ZktBH-UfJ7w=",
			"name": "AssassinBot",
			"server_era": "01cwcmytc5slc",
			"server_id": "heim.3",
			"session_id": "5a6b7442482d55664a37773d-6d4d86ecae939c59"
		})
		self.assertEqual(s.session_type(), "bot"                                      )
		self.assertEqual(s.user_id(),      "bot:ZktBH-UfJ7w="                         )
		self.assertEqual(s.session_id(),   "5a6b7442482d55664a37773d-6d4d86ecae939c59")
		self.assertEqual(s.name(),         "AssassinBot"                              )
		self.assertEqual(s.mentionable(),  "AssassinBot"                              )
		self.assertEqual(s.listable(5),    ("", "Assa…")                              )
		self.assertEqual(s.listable(10),   ("", "AssassinB…")                         )
		self.assertEqual(s.listable(50),   ("", "AssassinBot")                        )
		self.assertEqual(s.server_id(),    "heim.3"                                   )
		self.assertEqual(s.server_era(),   "01cwcmytc5slc"                            )
		self.assertEqual(s.is_staff(),     False                                      )
		self.assertEqual(s.is_manager(),   False                                      )
		
		s = session.Session({
			"id": "account:ZktBH-UfJ7w=",
			"name": "my h^nds @re typin' wurd$",
			"server_era": "01cwcmytc5slc",
			"server_id": "heim.3",
			"session_id": "5a6b7442482d55664a37773d-6d4d86ecae939c59",
			"is_staff": True
		})
		self.assertEqual(s.session_type(), "account"                          )
		self.assertEqual(s.name(),         "my h^nds @re typin' wurd$"        )
		self.assertEqual(s.mentionable(),  "myh^nds@retypinwurd$"             )
		self.assertEqual(s.listable(5),    ("*s", "my…")                      )
		self.assertEqual(s.listable(10),   ("*s", "my h^nd…")                 )
		self.assertEqual(s.listable(50),   ("*s", "my h^nds @re typin' wurd$"))
		self.assertEqual(s.is_staff(),     True                               )
		self.assertEqual(s.is_manager(),   False                              )
		
		s = session.Session({
			"id": "account:ZktBH-UfJ7w=",
			"name": "greenie",
			"server_era": "01cwcmytc5slc",
			"server_id": "heim.3",
			"session_id": "5a6b7442482d55664a37773d-6d4d86ecae939c59",
			"is_staff": True,
			"is_manager": True
		})
		self.assertEqual(s.mentionable(), "greenie"         )
		self.assertEqual(s.listable(5),   ("*ms", "g…")     )
		self.assertEqual(s.listable(9),   ("*ms", "green…") )
		self.assertEqual(s.listable(10),  ("*ms", "greenie"))
		self.assertEqual(s.is_staff(),    True              )
		self.assertEqual(s.is_manager(),  True              )

if __name__ == '__main__':
	unittest.main()
