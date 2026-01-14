import serial
import os
import sys
import csv
import statistics
import time

from UART_comp_data import UartData
from UART_comp_meas import UartMeas

# --- CONFIGURATION ---
RUN_COUNT = 5            # Sets amount of runs to average
SAVE_ALL_RUNS = True     # False - only save averages from runs, True - save all raw data
PORT = "COM5"            # Select COM port
BAUD = 38400             # Set baud rate
# ---------------------

# Generates .cvs report
def save_benchmark_report(filepath, result_list, pc_times, stats):
    """
    Creates csv report.  
    """
    try:
        with open(filepath, 'w', newline='') as f:
            f.write("sep=,\n")
            repwriter = csv.writer(f)
            
            # Global prints
            repwriter.writerow(["# BENCHMARK REPORT"])
            repwriter.writerow(["Input File", stats['Input_File']])
            repwriter.writerow(["Baud Rate", BAUD])
            repwriter.writerow(["Iterations", RUN_COUNT])
            repwriter.writerow([])
            
            total_in = sum(b['in_len'] for b in result_list[0])
            total_out = sum(b['out_len'] for b in result_list[0])
            
            repwriter.writerow(["# GLOBAL PARAMETERS"])
            repwriter.writerow(["Parameter", "Value", "Unit"])
            repwriter.writerow(["Compression Ratio", stats['Global_CR'], "Ratio"])
            repwriter.writerow(["Efficiency (E)", stats['Avg_Efficiency'], "Bytes/us"])
            repwriter.writerow(["Link Speedup (Eta)", stats['Avg_Tx_Efficiency'], "x"])
            repwriter.writerow(["Avg Latency", stats['Avg_Latency_ms'], "ms"])
            repwriter.writerow(["Jitter", stats['Jitter_ms'], "ms"])
            repwriter.writerow([])

            # Per-Block Averages
            repwriter.writerow(["# PER-BLOCK AVERAGES"])
            header = ["Block_ID", "In_Bytes", "Out_Bytes", "Avg_Ratio", "Avg_MCU_us", "Avg_PC_us"]
            repwriter.writerow(header)
            
            num_blocks = len(result_list[0])
            for i in range(num_blocks):
                ratios = [run[i]['ratio'] for run in result_list if i < len(run)]
                mcu_vals = [run[i]['comp_us'] for run in result_list if i < len(run)]
                pc_vals = [run_lats[i] for run_lats in pc_times if i < len(run_lats)]
                
                repwriter.writerow([
                    result_list[0][i]['block_id'],
                    result_list[0][i]['in_len'],
                    result_list[0][i]['out_len'],
                    f"{statistics.mean(ratios):.4f}",
                    f"{statistics.mean(mcu_vals):.2f}",
                    f"{statistics.mean(pc_vals):.2f}"
                ])

            # Raw data print for all blocks
            if SAVE_ALL_RUNS:
                repwriter.writerow([])
                repwriter.writerow(["# RAW DATA "])
                repwriter.writerow(["Iteration", "Block_ID", "Ratio", "MCU_us", "PC_us"])
                for run_idx, run_data in enumerate(result_list):
                    for b_idx, block in enumerate(run_data):
                        pc_val = pc_times[run_idx][b_idx] if b_idx < len(pc_times[run_idx]) else 0
                        repwriter.writerow([
                            run_idx + 1,
                            block['block_id'],
                            f"{block['ratio']:.4f}",
                            block['comp_us'],
                            f"{pc_val:.2f}"
                        ])
                        
        print(f"Report generated: {filepath}")
    except Exception as e:
        print(f"Error generating CSV: {e}")
# Main function - responsible for overall UART communications and averaging
# Also performs calculations for averaged data
def run_benchmark(input_file):
    if not os.path.exists(input_file):
        print(f"Error: '{input_file}' not found."); return

    out_file = input("Enter output CSV file name: ").strip()
    if not out_file.lower().endswith('.csv'): out_file += '.csv'

    bin_out_file = os.path.splitext(input_file)[0] + ".bin"

    iteration_pc_tim_total = []
    iteration_result_total = []

    try:
        with serial.Serial(PORT, BAUD, timeout=2) as ser:
            data_handler = UartData(ser)
            meas_handler = UartMeas(ser)

            with open(input_file, "rb") as f:
                file_data = f.read()

            print(f"\n--- Running {RUN_COUNT} Iterations for {input_file} ---")
            
            for run in range(RUN_COUNT):
                iteration_lat = []
                compressed_chunks = []  
                
                data_handler.send_initial_header(len(file_data))
                
                for i in range(0, len(file_data), 512):
                    chunk = file_data[i : i+512]
                    
                    rx_data, duration_pc = data_handler.exchange_block(chunk)
                    
                    iteration_lat.append(duration_pc)
                    compressed_chunks.append(rx_data)
                
                iteration_pc_tim_total.append(iteration_lat)

                if run == 0:
                    try:
                        with open(bin_out_file, "wb") as bf:
                            for block in compressed_chunks:
                                bf.write(block)
                        print(f"  Binary data saved to: {bin_out_file}")
                    except Exception as b_err:
                        print(f"  Warning: Could not save binary file: {b_err}")
                
                run_tele = meas_handler.fetch_and_parse()
                if not run_tele:
                    print(f"Error: Iteration {run+1} failed to receive data.")
                iteration_result_total.append(run_tele)
                
                print(f" Iteration {run+1}/{RUN_COUNT} complete...")

            if not iteration_result_total or not iteration_result_total[0]:
                print("Error: No data received.")
                return

            # --- Calculations ---
            total_pc_ms = [sum(run) / 1000 for run in iteration_pc_tim_total]
            Avg_Latency_ms = statistics.mean(total_pc_ms)
            jitter_ms = statistics.stdev(total_pc_ms) if len(total_pc_ms) > 1 else 0

            iter_in_total = [sum(b['in_len'] for b in run) for run in iteration_result_total]
            iter_out_total = [sum(b['out_len'] for b in run) for run in iteration_result_total]
            iter_comp_total_us = [sum(b['comp_us'] for b in run) for run in iteration_result_total]

            avg_in = statistics.mean(iter_in_total)
            avg_out = statistics.mean(iter_out_total)
            avg_comp_us = statistics.mean(iter_comp_total_us)

            Global_CR = avg_out / avg_in if avg_in > 0 else 0

            Avg_Efficiency = (avg_in - avg_out) / avg_comp_us if avg_comp_us > 0 else 0

            raw_time_us = (avg_in / (BAUD / 10)) * 1_000_000
            avg_total_pc_us = Avg_Latency_ms * 1000
            eta_avg = raw_time_us / avg_total_pc_us if avg_total_pc_us > 0 else 0

            global_stats = {
                "Input_File": input_file,
                "Global_CR": f"{Global_CR:.4f}",
                "Avg_Efficiency": f"{Avg_Efficiency:.4f}",
                "Avg_Tx_Efficiency": f"{eta_avg:.2f}",
                "Avg_Latency_ms": f"{Avg_Latency_ms:.2f}",
                "Jitter_ms": f"{jitter_ms:.4f}"
            }

            save_benchmark_report(out_file, iteration_result_total, iteration_pc_tim_total, global_stats)
            
            print(f"\n--- Summary ---")
            print(f"Avg Speedup (Eta): {global_stats['Avg_Tx_Efficiency']}x")
            print(f"Efficiency (E):    {global_stats['Avg_Efficiency']} B/us")
            print(f"Jitter:         {global_stats['Jitter_ms']} ms")

    except Exception as e:
        print(f"\nBenchmark Failed: {e}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else input("File: ").strip().replace('"', '')
    run_benchmark(target)
