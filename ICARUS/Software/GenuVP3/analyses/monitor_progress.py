from time import sleep
from typing import Any, Optional
from numpy import dtype, floating, ndarray
from tqdm.auto import tqdm
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

from ICARUS.Software.GenuVP3.postProcess.progress import latest_time

def serial_monitor(
    progress_bars: list[tqdm],
    CASEDIR: str,
    position: int,
    lock: Optional[Lock],
    max_iter: int,
    refresh_progress: float,
)-> None:
    sleep(1 + (position+1)/10)

    while True:
        sleep(refresh_progress)
        time, error = latest_time(CASEDIR)

        if error:
            progress_bars[position].write(f"Analysis encountered Error")
            break
        
        if time is None:
            continue

        if lock:
            with lock:
                progress_bars[position].n = int(time)
                progress_bars[position].refresh(nolock=True)
        else:
            progress_bars[position].n = int(time)
            progress_bars[position].refresh(nolock=True)

        if time>=max_iter:
            break


def parallel_monitor(
        CASEDIRS: list[str],
        angles: list[float] | ndarray[Any, dtype[floating[Any]]],
        max_iter: int,
        refresh_progress: float = 0.2
)-> None:
    # Create a lock to synchronize progress bar updates
    progress_bar_lock = Lock()

    # Create a list to store progress bars
    progress_bars = []

    with ThreadPoolExecutor(max_workers=len(angles)) as executor:
        for i,angle in enumerate(angles):
            pbar = tqdm(
                total=max_iter,
                desc=f"\t\t{angle} Progress:",
                position=i,
                leave=True,
                colour='#cc3300',
                bar_format="{l_bar}{bar:30}{r_bar}"
            )
            progress_bars.append(pbar)

            # Start the progress update in parallel using ThreadPoolExecutor
            executor.submit(
                serial_monitor,
                progress_bars = progress_bars,
                CASEDIR = CASEDIRS[i],
                position= i,
                lock = progress_bar_lock,
                max_iter = max_iter,
                refresh_progress = refresh_progress,
            )
    
    for pbar in progress_bars:
        pbar.close()