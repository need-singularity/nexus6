#!/usr/bin/env python3
"""
OpenBCI Cyton+Daisy 16ch EEG Data Collector
TECS-L Project: G=D×P/I Model Verification

Usage:
    source eeg_env/bin/activate
    python eeg/collect.py --duration 60        # 60초 수집
    python eeg/collect.py --duration 300 --tag resting_eyes_closed
"""

import argparse
import time
import json
import os
from datetime import datetime

import numpy as np
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter


# 10-20 system channel labels for Cyton+Daisy 16ch
CHANNEL_LABELS_16 = [
    'Fp1', 'Fp2', 'C3', 'C4', 'P7', 'P8', 'O1', 'O2',  # Cyton 8ch
    'F7', 'F8', 'F3', 'F4', 'T7', 'T8', 'P3', 'P4',     # Daisy 8ch
]
CHANNEL_LABELS_8 = CHANNEL_LABELS_16[:8]

# EEG frequency bands
BANDS = {
    'delta':  (0.5, 4),
    'theta':  (4, 8),
    'alpha':  (8, 12),
    'beta':   (13, 30),
    'gamma':  (30, 100),
}


def find_serial_port():
    """Auto-detect OpenBCI dongle serial port on macOS."""
    import glob
    ports = glob.glob('/dev/tty.usbserial*') + glob.glob('/dev/cu.usbserial*')
    if ports:
        return ports[0]
    # fallback: try common names
    ports = glob.glob('/dev/tty.usbmodem*') + glob.glob('/dev/cu.usbmodem*')
    if ports:
        return ports[0]
    return None


def collect_eeg(duration_sec=60, board_type='cyton_daisy', serial_port=None, tag=''):
    """Collect EEG data from OpenBCI board."""

    # Board selection
    if board_type == 'cyton_daisy':
        board_id = BoardIds.CYTON_DAISY_BOARD.value
        ch_labels = CHANNEL_LABELS_16
    elif board_type == 'cyton':
        board_id = BoardIds.CYTON_BOARD.value
        ch_labels = CHANNEL_LABELS_8
    else:
        # Synthetic board for testing without hardware
        board_id = BoardIds.SYNTHETIC_BOARD.value
        ch_labels = [f'ch{i}' for i in range(16)]

    params = BrainFlowInputParams()

    if board_type in ('cyton', 'cyton_daisy'):
        if serial_port is None:
            serial_port = find_serial_port()
        if serial_port is None:
            print("ERROR: OpenBCI dongle not found. Available ports:")
            import glob
            print(glob.glob('/dev/tty.*'))
            print("\nUse --port to specify, or --board synthetic to test without hardware")
            return None
        params.serial_port = serial_port
        print(f"Serial port: {serial_port}")

    # Initialize board
    BoardShim.enable_dev_board_logger()
    board = BoardShim(board_id, params)

    print(f"Board: {board_type} ({len(ch_labels)}ch)")
    print(f"Duration: {duration_sec}s")
    print(f"Tag: {tag or 'none'}")
    print()

    try:
        board.prepare_session()
        sample_rate = BoardShim.get_sampling_rate(board_id)
        eeg_channels = BoardShim.get_eeg_channels(board_id)
        print(f"Sample rate: {sample_rate} Hz")
        print(f"EEG channels: {len(eeg_channels)}")
        print()

        # Start streaming
        board.start_stream()
        print(f"Recording started... ({duration_sec}s)")

        # Progress indicator
        start = time.time()
        while time.time() - start < duration_sec:
            elapsed = int(time.time() - start)
            remaining = duration_sec - elapsed
            print(f"\r  {elapsed}/{duration_sec}s ({remaining}s remaining)", end='', flush=True)
            time.sleep(1)

        print(f"\r  {duration_sec}/{duration_sec}s - Done!          ")

        # Get data
        data = board.get_board_data()
        board.stop_stream()
        board.release_session()

    except Exception as e:
        print(f"ERROR: {e}")
        try:
            board.release_session()
        except:
            pass
        return None

    # Extract EEG channels
    eeg_data = data[eeg_channels[:len(ch_labels)], :]
    timestamp = data[BoardShim.get_timestamp_channel(board_id), :]
    n_samples = eeg_data.shape[1]

    print(f"\nCollected: {n_samples} samples ({n_samples/sample_rate:.1f}s)")
    print(f"Shape: {eeg_data.shape} (channels x samples)")

    # Save data
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    tag_str = f"_{tag}" if tag else ""
    filename = f"eeg_{timestamp_str}{tag_str}"

    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)

    # Save raw numpy
    np.save(os.path.join(data_dir, f"{filename}.npy"), eeg_data)

    # Save metadata
    meta = {
        'timestamp': timestamp_str,
        'tag': tag,
        'board': board_type,
        'channels': ch_labels[:eeg_data.shape[0]],
        'sample_rate': sample_rate,
        'duration_sec': duration_sec,
        'n_samples': n_samples,
        'n_channels': eeg_data.shape[0],
        'bands': BANDS,
    }
    with open(os.path.join(data_dir, f"{filename}_meta.json"), 'w') as f:
        json.dump(meta, f, indent=2)

    # Save CSV for easy inspection
    import pandas as pd
    df = pd.DataFrame(eeg_data.T, columns=ch_labels[:eeg_data.shape[0]])
    df.insert(0, 'timestamp', timestamp[:n_samples])
    df.to_csv(os.path.join(data_dir, f"{filename}.csv"), index=False)

    filepath = os.path.join(data_dir, filename)
    print(f"\nSaved:")
    print(f"  {filepath}.npy  (raw numpy)")
    print(f"  {filepath}.csv  (spreadsheet)")
    print(f"  {filepath}_meta.json  (metadata)")

    return filepath


def main():
    parser = argparse.ArgumentParser(description='OpenBCI EEG Data Collector')
    parser.add_argument('--duration', type=int, default=60, help='Recording duration in seconds')
    parser.add_argument('--board', choices=['cyton', 'cyton_daisy', 'synthetic'],
                        default='cyton_daisy', help='Board type')
    parser.add_argument('--port', type=str, default=None, help='Serial port (auto-detect if omitted)')
    parser.add_argument('--tag', type=str, default='', help='Tag for this recording (e.g. resting_eyes_closed)')
    args = parser.parse_args()

    collect_eeg(
        duration_sec=args.duration,
        board_type=args.board,
        serial_port=args.port,
        tag=args.tag,
    )


if __name__ == '__main__':
    main()
