import sys
import unittest
import threading
from unittest.mock import MagicMock, patch

sys.modules["py4godot"] = MagicMock()
sys.modules["py4godot.classes"] = MagicMock()
sys.modules["py4godot.classes.Node3D"] = MagicMock()

from server.client_handler import ClientHandler  # noqa: E402
from server.client_state_manager import ClientState  # noqa: E402
from server.logger import ServerLogger  # noqa: E402
from server.player_manager import PlayerManager  # noqa: E402
from server.packets import INIT_PACKET  # noqa: E402


class MockNode3D:
    """Mock Node3D for testing."""

    def __init__(self):
        self.name = ""
        self.children = []
        self.freed = False

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def call_deferred(self, method, *args):
        if method == "add_child":
            self.children.append(args[0])
        elif method == "queue_free":
            self.freed = True


class MockSocket:
    """Mock socket for testing."""

    def __init__(self):
        self.sent_data = []
        self.closed = False
        self.should_fail_send = False
        self.recv_data = b""

    def send(self, data):
        if self.should_fail_send:
            raise ConnectionError("Send failed")
        self.sent_data.append(data)

    def recv(self, size):
        if self.recv_data:
            data = self.recv_data
            self.recv_data = b""
            return data
        return b""

    def settimeout(self, timeout):
        pass  # Mock implementation

    def close(self):
        self.closed = True


class TestClientHandler(unittest.TestCase):
    """Test ClientHandler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = MagicMock(spec=ServerLogger)
        self.mock_player_manager = MagicMock(spec=PlayerManager)
        self.mock_parent_node = MockNode3D()

        self.client_handler = ClientHandler(
            self.mock_logger, self.mock_player_manager, self.mock_parent_node
        )

    def test_initialization(self):
        """Test ClientHandler initialization."""
        self.assertFalse(self.client_handler.is_running)
        self.assertEqual(len(self.client_handler.client_nodes), 0)
        self.assertIsNotNone(self.client_handler.state_manager)

    @patch("socket.socket")
    def test_start_handling_accept_connection(self, mock_socket_class):
        """Test handling new client connection."""
        mock_server_socket = MagicMock()
        mock_client_socket = MockSocket()
        address = ("127.0.0.1", 12345)
        player_index = 0x5000

        mock_server_socket.accept.return_value = (mock_client_socket, address)
        result = player_index
        self.mock_player_manager.get_next_player_index.return_value = result

        call_count = 0

        def mock_is_running():
            nonlocal call_count
            call_count += 1
            return call_count == 1

        handler_thread = threading.Thread(
            target=self.client_handler.start_handling,
            args=(mock_server_socket, mock_is_running),
        )
        handler_thread.start()
        handler_thread.join(timeout=1)

        mock_server_socket.accept.assert_called_once()

        self.mock_player_manager.get_next_player_index.assert_called_once()
        expected_call = (player_index, address)
        self.mock_player_manager.add_player.assert_called_once_with(*expected_call)

        self.assertIn(INIT_PACKET, mock_client_socket.sent_data)

        expected_msg = (
            f"Sent init packet to player 0x{player_index:04X}: "
            f"{INIT_PACKET.hex().upper()}"
        )
        self.mock_logger.debug.assert_any_call(expected_msg)

    def test_reject_connection_max_players(self):
        """Test rejecting connection when max players reached."""
        mock_server_socket = MagicMock()
        mock_client_socket = MockSocket()
        address = ("127.0.0.1", 12345)

        mock_server_socket.accept.return_value = (mock_client_socket, address)

        result = None
        self.mock_player_manager.get_next_player_index.return_value = result

        call_count = 0

        def mock_is_running():
            nonlocal call_count
            call_count += 1
            return call_count == 1

        handler_thread = threading.Thread(
            target=self.client_handler.start_handling,
            args=(mock_server_socket, mock_is_running),
        )
        handler_thread.start()
        handler_thread.join(timeout=1)

        self.assertTrue(mock_client_socket.closed)
        expected_msg = (
            f"Rejecting connection from {address}: " f"Maximum players reached"
        )
        self.mock_logger.warning.assert_called_with(expected_msg)

    def test_init_packet_send_failure(self):
        """Test handling of init packet send failure."""
        mock_server_socket = MagicMock()
        mock_client_socket = MockSocket()
        mock_client_socket.should_fail_send = True
        address = ("127.0.0.1", 12345)
        player_index = 0x5000

        mock_server_socket.accept.return_value = (mock_client_socket, address)
        result = player_index
        self.mock_player_manager.get_next_player_index.return_value = result

        call_count = 0

        def mock_is_running():
            nonlocal call_count
            call_count += 1
            return call_count == 1

        handler_thread = threading.Thread(
            target=self.client_handler.start_handling,
            args=(mock_server_socket, mock_is_running),
        )
        handler_thread.start()
        handler_thread.join(timeout=1)

        self.mock_player_manager.remove_player.assert_called_with(player_index)
        self.mock_logger.log_exception.assert_called()

    def test_node_creation_and_naming(self):
        """Test that client nodes are created with correct names."""
        player_index = 0x5000
        expected_name = f"Player_{player_index:04X}"

        with patch("server.client_handler.Node3D") as mock_node_class:
            mock_node = MockNode3D()
            mock_node_class.return_value = mock_node

            mock_server_socket = MagicMock()
            mock_client_socket = MockSocket()
            address = ("127.0.0.1", 12345)

            accept_result = (mock_client_socket, address)
            mock_server_socket.accept.return_value = accept_result
            mgr = self.mock_player_manager
            mgr.get_next_player_index.return_value = player_index

            call_count = 0

            def mock_is_running():
                nonlocal call_count
                call_count += 1
                return call_count == 1

            handler_thread = threading.Thread(
                target=self.client_handler.start_handling,
                args=(mock_server_socket, mock_is_running),
            )
            handler_thread.start()
            handler_thread.join(timeout=1)

            self.assertEqual(mock_node.name, expected_name)

    def test_handle_client_communication(self):
        """Test client message handling (echo functionality)."""
        mock_socket = MagicMock()
        address = ("127.0.0.1", 12345)
        player_index = 0x5000
        test_data = b"test message"

        mock_socket.recv.side_effect = [test_data, b""]

        def mock_is_running():
            return True

        client_thread = threading.Thread(
            target=self.client_handler._handle_client_communication,
            args=(mock_socket, address, player_index, mock_is_running),
        )
        client_thread.start()
        client_thread.join(timeout=1)

        mock_socket.send.assert_called_with(test_data)

        self.mock_logger.debug.assert_any_call(
            f"Received from player 0x{player_index:04X}: {test_data.hex().upper()}"
        )

    def test_client_disconnect_cleanup(self):
        """Test cleanup when client disconnects."""
        mock_socket = MagicMock()
        address = ("127.0.0.1", 12345)
        player_index = 0x5000

        mock_node = MockNode3D()
        self.client_handler.client_nodes[player_index] = mock_node

        mock_socket.recv.return_value = b""

        def mock_is_running():
            return True

        client_thread = threading.Thread(
            target=self.client_handler._handle_client_communication,
            args=(mock_socket, address, player_index, mock_is_running),
        )
        client_thread.start()
        client_thread.join(timeout=1)

        mock_socket.close.assert_called()
        self.mock_player_manager.remove_player.assert_called_with(player_index)
        self.assertTrue(mock_node.freed)
        self.assertNotIn(player_index, self.client_handler.client_nodes)

    def test_stop_handling(self):
        """Test stopping the client handler."""
        player1 = 0x5001
        player2 = 0x5002
        mock_node1 = MockNode3D()
        mock_node2 = MockNode3D()

        self.client_handler.client_nodes[player1] = mock_node1
        self.client_handler.client_nodes[player2] = mock_node2

        self.client_handler.stop_handling()

        self.assertFalse(self.client_handler.is_running)

        self.assertTrue(mock_node1.freed)
        self.assertTrue(mock_node2.freed)
        self.assertEqual(len(self.client_handler.client_nodes), 0)

    def test_get_client_node(self):
        """Test getting client node by player index."""
        player_index = 0x5000
        mock_node = MockNode3D()

        self.client_handler.client_nodes[player_index] = mock_node

        retrieved_node = self.client_handler.get_client_node(player_index)
        self.assertIs(retrieved_node, mock_node)

        non_existent_node = self.client_handler.get_client_node(99999)
        self.assertIsNone(non_existent_node)

    def test_state_manager_integration(self):
        """Test integration with state manager."""
        player_index = 0x5000

        self.assertIsNotNone(self.client_handler.state_manager)

        state_mgr = self.client_handler.state_manager
        with patch.object(state_mgr, "add_client") as mock_add:
            with patch.object(state_mgr, "transition_state") as mock_transition:
                mock_transition.return_value = True

                mock_server_socket = MagicMock()
                mock_client_socket = MockSocket()
                address = ("127.0.0.1", 12345)

                # Create a mock login packet (longer than 12 bytes)
                # Include header (18 bytes) + some login data
                header = b"\x00" * 18
                login_data = (
                    b"user\x01password\x00"  # login + delimiter + password + terminator
                )
                mock_login_packet = header + login_data

                # Mock the recv method to return the login packet when called
                mock_client_socket.recv_data_queue = [mock_login_packet]
                original_recv = mock_client_socket.recv

                def mock_recv(size):
                    if (
                        hasattr(mock_client_socket, "recv_data_queue")
                        and mock_client_socket.recv_data_queue
                    ):
                        return mock_client_socket.recv_data_queue.pop(0)
                    return original_recv(size)

                mock_client_socket.recv = mock_recv

                accept_result = (mock_client_socket, address)
                mock_server_socket.accept.return_value = accept_result
                mgr = self.mock_player_manager
                mgr.get_next_player_index.return_value = player_index

                call_count = 0

                def mock_is_running():
                    nonlocal call_count
                    call_count += 1
                    return call_count == 1

                handler_thread = threading.Thread(
                    target=self.client_handler.start_handling,
                    args=(mock_server_socket, mock_is_running),
                )
                handler_thread.start()
                handler_thread.join(timeout=1)

                # Since client operations now happen asynchronously, we need to wait
                # for the client thread to complete its initialization
                import time

                max_wait = 5.0  # Increased wait time for authentication flow
                wait_interval = 0.1  # Check interval
                elapsed = 0

                while elapsed < max_wait:
                    if mock_add.called and mock_transition.called:
                        break
                    time.sleep(wait_interval)
                    elapsed += wait_interval

                mock_add.assert_called_with(player_index)

                self.assertTrue(mock_transition.called)
                # Verify the first transition call is to INIT_READY_FOR_INITIAL_DATA
                mock_transition.assert_any_call(
                    player_index, ClientState.INIT_READY_FOR_INITIAL_DATA
                )

    def test_character_selection_waiting_loop(self):
        """Test character selection waiting loop functionality."""
        player_index = 0x5000
        mock_socket = MagicMock()

        # Test 1: Character delete request (starts with 0x2A)
        delete_packet = b"\x2a" + b"\x00" * 17  # Make sure it's at least 18 bytes
        mock_socket.recv.return_value = delete_packet

        with patch.object(self.client_handler, "_cleanup_client") as mock_cleanup:
            with patch.object(
                self.client_handler.state_manager,
                "get_user_id",
                return_value="testuser",
            ):
                with patch.object(
                    self.client_handler.character_db,
                    "delete_character_by_user_index",
                    return_value=True,
                ):
                    result = self.client_handler._wait_for_character_screen(
                        mock_socket, player_index
                    )

                    self.assertFalse(result)
                    mock_cleanup.assert_called_once_with(mock_socket, player_index)
                    self.mock_logger.debug.assert_any_call("Requested character delete")

    def test_character_selection_invalid_packet(self):
        """Test character selection with invalid packet conditions."""
        player_index = 0x5000
        mock_socket = MagicMock()

        # Test invalid packet: buffer[0] < 0x1B
        invalid_packet = b"\x1a" + b"\x00" * 16
        # Create a valid character creation packet (30 bytes total)
        valid_packet = bytearray(30)
        valid_packet[0] = 30  # Packet length >= 0x1B
        valid_packet[13] = 0x08
        valid_packet[14] = 0x40
        valid_packet[15] = 0x80
        valid_packet[16] = 0x05
        valid_packet[17] = 8  # Character slot

        # Return invalid packet first, then valid packet
        mock_socket.recv.side_effect = [invalid_packet, bytes(valid_packet)]

        with patch.object(
            self.client_handler.state_manager, "get_user_id", return_value="testuser"
        ):
            with patch.object(
                self.client_handler, "_create_character_from_packet", return_value=True
            ):
                with patch(
                    "server.packets.ServerPackets.character_name_check_success"
                ) as mock_success:
                    with patch("utils.socket_utils.SocketUtils.send") as mock_send:
                        mock_success.return_value = b"success_packet"
                        mock_send.return_value = True

                        result = self.client_handler._wait_for_character_screen(
                            mock_socket, player_index
                        )

                        # Should return the character slot index (1 in this case: 8 // 4 - 1 = 1)
                        self.assertEqual(result, 1)
                        mock_success.assert_called_once_with(player_index)
                        mock_send.assert_called_once()

    def test_character_selection_valid_packet(self):
        """Test character selection with valid packet."""
        player_index = 0x5000
        mock_socket = MagicMock()

        # Create a valid character creation packet (30 bytes total)
        valid_packet = bytearray(30)
        valid_packet[0] = 30  # Packet length >= 0x1B
        valid_packet[13] = 0x08
        valid_packet[14] = 0x40
        valid_packet[15] = 0x80
        valid_packet[16] = 0x05
        valid_packet[17] = 8  # Character slot
        mock_socket.recv.return_value = bytes(valid_packet)

        with patch.object(
            self.client_handler.state_manager, "get_user_id", return_value="testuser"
        ):
            with patch.object(
                self.client_handler, "_create_character_from_packet", return_value=True
            ):
                with patch(
                    "server.packets.ServerPackets.character_name_check_success"
                ) as mock_success:
                    with patch("utils.socket_utils.SocketUtils.send") as mock_send:
                        mock_success.return_value = b"success_packet"
                        mock_send.return_value = True

                        result = self.client_handler._wait_for_character_screen(
                            mock_socket, player_index
                        )

                        # Should return the character slot index (1 in this case: 8 // 4 - 1 = 1)
                        self.assertEqual(result, 1)
                        mock_success.assert_called_once_with(player_index)
                        mock_send.assert_called_once_with(
                            mock_socket,
                            b"success_packet",
                            player_index,
                            self.mock_logger,
                            f"Sent character name check success to player "
                            f"0x{player_index:04X}: {b'success_packet'.hex().upper()}",
                        )
                        self.mock_logger.info.assert_any_call(
                            f"Character creation completed for player 0x{player_index:04X}"
                        )

    # def test_send_enter_game_data(self):
    #     """Test send_enter_game_data method."""
    #     player_index = 0x5000
    #     character_slot_index = 1
    #     user_id = "testuser"
    #     mock_socket = MagicMock()

    #     # Mock the state manager to return user_id
    #     with patch.object(
    #         self.client_handler.state_manager, "get_user_id", return_value=user_id
    #     ):
    #         # Mock the character database to return character data
    #         mock_character_data = {
    #             "_id": "test_id",
    #             "user_id": user_id,
    #             "character_slot_index": character_slot_index,
    #             "name": "TestChar",
    #             "is_gender_female": False,
    #             "face_type": 1,
    #             "hair_style": 1,
    #             "hair_color": 1,
    #             "tattoo": 0,
    #             "is_not_queued_for_deletion": True,
    #         }

    #         with patch.object(
    #             self.client_handler.character_db.characters,
    #             "find_one",
    #             return_value=mock_character_data,
    #         ):
    #             # Mock SocketUtils.send
    #             with patch(
    #                 "utils.socket_utils.SocketUtils.send", return_value=True
    #             ) as mock_send:
    #                 # Call the method
    #                 self.client_handler.send_enter_game_data(
    #                     character_slot_index, player_index, mock_socket
    #                 )

    #                 # Check if any exception was logged
    #                 if self.mock_logger.log_exception.called:
    #                     print("Exception was logged:")
    #                     for call in self.mock_logger.log_exception.call_args_list:
    #                         print(f"  {call}")

    #                 # Check if any error was logged
    #                 if self.mock_logger.error.called:
    #                     print("Error was logged:")
    #                     for call in self.mock_logger.error.call_args_list:
    #                         print(f"  {call}")

    #                 # Verify that send was called
    #                 self.assertTrue(mock_send.called, "SocketUtils.send was not called")
    #                 call_args = mock_send.call_args

    #                 # Verify the socket and player_index were passed correctly
    #                 self.assertEqual(call_args[0][0], mock_socket)  # client_socket
    #                 self.assertEqual(call_args[0][2], player_index)  # player_index

    #                 # Verify that game data was generated (should be a bytearray)
    #                 game_data = call_args[0][1]  # game_data
    #                 self.assertIsInstance(game_data, (bytes, bytearray))
    #                 self.assertGreater(len(game_data), 0)

    #                 # Verify success message was logged
    #                 self.mock_logger.info.assert_any_call(
    #                     f"Successfully sent enter game data for character 'TestChar' "
    #                     f"at slot {character_slot_index} to player 0x{player_index:04X} "
    #                     f"({len(game_data)} bytes)"
    #                 )

    def test_send_enter_game_data_no_user_id(self):
        """Test send_enter_game_data when no user_id is found."""
        player_index = 0x5000
        character_slot_index = 1
        mock_socket = MagicMock()

        # Mock the state manager to return None for user_id
        with patch.object(
            self.client_handler.state_manager, "get_user_id", return_value=None
        ):
            # Call the method
            self.client_handler.send_enter_game_data(
                character_slot_index, player_index, mock_socket
            )

            # Verify error was logged
            self.mock_logger.error.assert_any_call(
                f"Cannot send enter game data for player 0x{player_index:04X} - no user_id found"
            )

    def test_send_enter_game_data_character_not_found(self):
        """Test send_enter_game_data when character is not found in database."""
        player_index = 0x5000
        character_slot_index = 1
        user_id = "testuser"
        mock_socket = MagicMock()

        # Mock the state manager to return user_id
        with patch.object(
            self.client_handler.state_manager, "get_user_id", return_value=user_id
        ):
            # Mock the character database to return None (character not found)
            with patch.object(
                self.client_handler.character_db.characters,
                "find_one",
                return_value=None,
            ):
                # Call the method
                self.client_handler.send_enter_game_data(
                    character_slot_index, player_index, mock_socket
                )

                # Verify error was logged
                self.mock_logger.error.assert_any_call(
                    f"Cannot send enter game data for player 0x{player_index:04X} - "
                    f"character not found at slot {character_slot_index}"
                )


if __name__ == "__main__":
    unittest.main()
