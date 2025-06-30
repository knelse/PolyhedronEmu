import socket
import threading
import time
from typing import Callable
from py4godot.classes import gdclass
from py4godot.classes.Node3D import Node3D
from server.client_state_manager import client_state_manager
from server.logger import server_logger
from server.player_manager import player_manager as player_manager_class
from server.utils.socket_utils import server_socket_utils
from server.packets import server_packets
from utils.bitstream_utils import simple_bit_stream


@gdclass
class player_ingame_handler(Node3D):
    """
    player_ingame_handler manages the ingame behavior and interactions for a player.
    This script is attached to the Player node (Node3D).
    """

    client_socket: socket.socket | None
    player_index: int | None
    logger: server_logger | None
    state_manager: client_state_manager | None
    user_id: str | None
    player_manager: player_manager_class | None
    is_running: Callable[[], bool] | None

    def __init__(self):
        super().__init__()
        self.client_socket = None
        self.player_index = None
        self.logger = None
        self.state_manager = None
        self.user_id = None
        self.player_manager = None
        self.is_running = None
        self.client_thread = None
        self._cleanup_done = False
        self.ping_should_xor_top_bit = False
        self.ping_counter = 0

    def start_ingame_handling(self) -> None:
        """Start the ingame communication handling in a separate thread."""
        if (
            self.client_socket is None
            or self.is_running is None
            or self.player_index is None
            or self.logger is None
        ):
            raise RuntimeError("Player not properly initialized")

        self.client_thread = threading.Thread(
            target=self._handle_ingame_communication, daemon=True
        )
        self.client_thread.start()

        msg = (
            f"Started ingame communication thread for player 0x{self.player_index:04X}"
        )
        self.logger.info(msg)

    def send_data(self, data: bytes) -> bool:
        """
        Send data to the client.

        Args:
            data: The data to send

        Returns:
           True if data was sent successfully, False otherwise
        """
        if not self.client_socket:
            return False

        try:
            self.client_socket.send(data)
            return True
        except OSError as e:
            if e.errno == 10038:  # WSAENOTSOCK - socket operation on non-socket
                player_idx = self.player_index or 0
                msg = f"Socket already closed for player 0x{player_idx:04X}"
                if self.logger:
                    self.logger.warning(msg)
            else:
                player_idx = self.player_index or 0
                msg = f"Socket error sending data to player 0x{player_idx:04X}"
                if self.logger:
                    self.logger.log_exception(msg, e)
            return False
        except Exception as e:
            player_idx = self.player_index or 0
            msg = f"Error sending data to player 0x{player_idx:04X}"
            if self.logger:
                self.logger.log_exception(msg, e)
            return False

    def handle_client_ping(self, data: bytes) -> bool:
        """
        Handle client ping packets that start with 0x26.

        Args:
            data: The received packet data

        Returns:
            True if ping was handled successfully, False otherwise
        """
        if len(data) < 30:
            return False

        client_ping_bytes = data[9:30]

        if len(client_ping_bytes) < 21:
            return False

        # Get byte 5 and potentially XOR it
        xored = client_ping_bytes[5]
        if self.ping_should_xor_top_bit:
            xored ^= 0b10000000

        if self.ping_counter == 0:
            first = ((client_ping_bytes[7] << 8) + client_ping_bytes[6]) & 0xFFFF
            first -= 0xE001
            self.ping_counter = (0xE001 + (first // 12)) & 0xFFFF

        stream = simple_bit_stream()
        stream.write_bytes(
            bytes(
                [
                    0x12,
                    0x00,
                    0x2C,
                    0x01,
                    0x00,
                    0xA1,
                    0x00,
                    0x8D,
                    0x0A,
                    0x32,
                    0xA0,
                    0x03,
                    0xE0,
                    0xE9,
                    0x0D,
                    0x01,
                    0x60,
                    0x00,
                ]
            )
        )
        # stream.write_bytes(client_ping_bytes[:5])
        # stream.write_int(xored, 8)
        # stream.write_int(self.ping_counter & 0xFF, 8)
        # stream.write_int((self.ping_counter >> 8) & 0xFF, 8)
        # stream.write_bytes(client_ping_bytes[8:12])
        # stream.write_bytes(bytes([0x00]))

        pong_packet = bytes(stream.to_bytes())

        success = self.send_data(pong_packet)

        if success and self.logger:
            player_idx = self.player_index or 0
            self.logger.debug(
                f"Sent pong response to player 0x{player_idx:04X}: {pong_packet.hex().upper()}"
            )

        self.ping_should_xor_top_bit = not self.ping_should_xor_top_bit
        self.ping_counter += 1

        if self.ping_counter < 0xE001 or self.ping_counter > 0xFFFF:
            self.ping_counter = 0xE001

        return success

    def _handle_ingame_communication(self) -> None:
        """
        Handle ongoing ingame communication with the client.
        This runs on a dedicated thread.
        """
        try:
            player_idx = self.player_index or 0
            msg = f"Started ingame communication loop for player 0x{player_idx:04X}"
            if self.logger:
                self.logger.debug(msg)

            last_transmission_end = time.time()
            last_keepalive_6s = time.time()
            last_keepalive_15s = time.time()

            while self.is_running():
                try:
                    current_time = time.time()

                    if current_time - last_transmission_end >= 3.0:
                        if self.send_data(server_packets.TRANSMISSION_END_PACKET):
                            if self.logger:
                                self.logger.debug(
                                    f"Sent TRANSMISSION_END_PACKET to player 0x{player_idx:04X}"
                                )
                        last_transmission_end = current_time

                    if current_time - last_keepalive_6s >= 6.0:
                        keepalive_packet = server_packets.keepalive_6_seconds(
                            player_idx
                        )
                        if self.send_data(keepalive_packet):
                            if self.logger:
                                self.logger.debug(
                                    f"Sent 6s keepalive to player 0x{player_idx:04X}"
                                )
                        last_keepalive_6s = current_time

                    if current_time - last_keepalive_15s >= 15.0:
                        keepalive_packet = server_packets.keepalive_15_seconds(
                            player_idx
                        )
                        if self.send_data(keepalive_packet):
                            if self.logger:
                                self.logger.debug(
                                    f"Sent 15s keepalive to player 0x{player_idx:04X}"
                                )
                        last_keepalive_15s = current_time

                    data = server_socket_utils.receive_packet_with_logging(
                        self.client_socket,
                        self.player_index,
                        self.logger,
                        1024,
                        10.0,
                        "ingame communication",
                    )

                    if not data:
                        break

                    # Handle client ping packets (starting with 0x26)
                    if data[0] == 0x26:
                        self.handle_client_ping(data)
                        continue

                    player_idx = self.player_index or 0
                    msg = (
                        f"Player 0x{player_idx:04X} sent ingame packet: "
                        f"{data.hex().upper()}"
                    )
                    if self.logger:
                        self.logger.debug(msg)

                except socket.timeout:
                    continue
                except ConnectionResetError:
                    player_idx = self.player_index or 0
                    msg = f"Player 0x{player_idx:04X} connection reset"
                    if self.logger:
                        self.logger.info(msg)
                    break
                except Exception as e:
                    player_idx = self.player_index or 0
                    msg = (
                        f"Error in ingame communication with player 0x{player_idx:04X}"
                    )
                    if self.logger:
                        self.logger.log_exception(msg, e)
                    break

        except Exception as e:
            player_idx = self.player_index or 0
            msg = f"Error in ingame communication thread for player 0x{player_idx:04X}"
            if self.logger:
                self.logger.log_exception(msg, e)
        finally:
            self._cleanup_player()

    def stop_handling(self) -> None:
        """Stop the ingame handling and clean up resources."""
        if self.client_thread and self.client_thread.is_alive():
            player_idx = self.player_index or 0
            msg = f"Stopping ingame handling for player 0x{player_idx:04X}"
            if self.logger:
                self.logger.info(msg)

            self.client_thread.join(timeout=5.0)

            if self.client_thread.is_alive():
                player_idx = self.player_index or 0
                msg = f"Ingame thread for player 0x{player_idx:04X} did not stop gracefully"
                if self.logger:
                    self.logger.warning(msg)

    def _cleanup_player(self) -> None:
        """
        Clean up all resources associated with this player.
        """
        if self._cleanup_done:
            return

        self._cleanup_done = True

        try:
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
        except Exception:
            pass

        if self.player_manager and self.player_index is not None:
            self.player_manager.release_index(self.player_index)

        if self.state_manager and self.player_index is not None:
            self.state_manager.cleanup_client(self.player_index)

        if self.player_index is not None:
            msg = f"Cleaned up ingame resources for player 0x{self.player_index:04X}"
            if self.logger:
                self.logger.debug(msg)

    def _ready(self) -> None:
        """Called when the node is ready. Handle character sheet setup and start ingame handling."""
        if self.logger and self.player_index is not None:
            msg = f"Player 0x{self.player_index:04X} ingame handler ready"
            self.logger.info(msg)

        character_sheet = self.get_node("character_sheet")
        if character_sheet and hasattr(character_sheet, "set_character_data"):
            if self.state_manager and hasattr(self.state_manager, "get_character_data"):
                character_data = self.state_manager.get_character_data(
                    self.player_index
                )
                if character_data:
                    character_sheet.set_character_data(character_data)

        self.start_ingame_handling()

    def _process(self, delta: float) -> None:
        """Called every frame."""
        pass

    def _exit_tree(self) -> None:
        """Called when the node is removed from the scene tree."""
        self.stop_handling()
