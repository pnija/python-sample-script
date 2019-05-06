VERSION = 1.1

import argparse
import threading
import csv
from processors import ProcessorParam
from processors import (
    LnProcessor
)

PROCESSOR_LIST = (
    IProcessor,
    LnProcessor
)

class ThreadProcessor(threading.Thread):
    def __init__(self, class_obj, name, *args, **kwargs):
        super(ThreadProcessor, self).__init__(*args, **kwargs)

        self.class_obj = class_obj
        self.name = name

    def run(self):
        self.class_obj.process()


parser = argparse.ArgumentParser(description='')

thread_list = []

def main():
    if not parsed.input_csv:
        raise RuntimeError("Need input csv")

    with open(parsed.input_csv, 'rb') as f:
        reader = csv.reader(f)
        next(reader, None)

        for row in reader:
            date_range_list = (date_from, date_to)

            params = ProcessorParam(
                position,
                keywords,
                country,
                state,
                city,
                hiring,
                date_range_list
            )

            for processor in PROCESSOR_LIST:
                p = processor(params)
                thread_processor = ThreadProcessor(p, p.__class__.__name__)
                thread_processor.start()
                thread_list.append(thread_processor)

            # LinkedInProcessor(params).process()

    while True:
        thread_finished = [(not t.is_alive(), t.name) for t in thread_list]

        if all([x[0] for x in thread_finished]):
            break
        else:
            finished_threads = [x for x in thread_finished if x[0]]
            finished_count = len(finished_threads)
            total_count = len(thread_finished)

            print('{}| {}%\r'.format(
                ','.join([x[1] for x in finished_threads]),
                round(float(finished_count)/float(total_count)*100.0, 2)
            )),

            sleep(1)

if __name__ == '__main__':
    main()
