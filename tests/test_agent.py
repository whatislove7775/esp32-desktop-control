import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[1] / "windows_agent" / "server.py"
spec = importlib.util.spec_from_file_location("desktop_agent", path)
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)

class AgentTests(unittest.TestCase):
    def test_magic_packet(self):
        packet = agent.magic_packet("AA:BB:CC:DD:EE:FF")
        self.assertEqual(len(packet), 102)
        self.assertEqual(packet[:6], b"\xff" * 6)
        self.assertEqual(packet[6:12], bytes.fromhex("AABBCCDDEEFF"))

    def test_invalid_mac(self):
        for value in ("", "AA:BB", "GG:BB:CC:DD:EE:FF", None):
            with self.assertRaises(ValueError):
                agent.magic_packet(value)

if __name__ == "__main__":
    unittest.main()
