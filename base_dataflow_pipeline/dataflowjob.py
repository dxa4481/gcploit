from __future__ import absolute_import

import argparse
import logging
import re
import sys
import threading
try:
    import thread
except ImportError:
    import _thread as thread

from past.builtins import unicode

import apache_beam as beam
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText
from apache_beam.options.pipeline_options import WorkerOptions, GoogleCloudOptions, PortableOptions, StandardOptions, DebugOptions, PipelineOptions, SetupOptions

class RunCommand(beam.DoFn):
    def __init__(self):
        pass

    def process(self, information=""):
        pass

# Decorator code taken from https://gist.github.com/aaronchall/6331661fe0185c30a0b4
def quit_function(fn_name):
    sys.stderr.flush() 
    thread.interrupt_main()

def exit_after(s):
    '''
    use as decorator to exit process if 
    function takes longer than s seconds
    '''
    def outer(fn):
        def inner(*args, **kwargs):
            timer = threading.Timer(s, quit_function, args=[fn.__name__])
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result
        return inner
    return outer

@exit_after(100)
def start_job(project, name, bucket, image, identity):
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--input',
      dest='input',
      default=f'gs://{bucket}/startup.sh',
      help='Input file to process.')
  parser.add_argument(
      '--output',
      dest='output',
      default=f'gs://{bucket}/output.txt',
      help='Output file to write results to.')
  parser.add_argument(
      '--extra_package',
      dest='extra_package',
      default='./a_package')
  known_args, pipeline_args = parser.parse_known_args()

  pipeline_options = PipelineOptions(pipeline_args)
  google_cloud_options = pipeline_options.view_as(GoogleCloudOptions)
  google_cloud_options.project = project
  google_cloud_options.job_name = name
  google_cloud_options.region = 'us-east1'
  google_cloud_options.staging_location = f'gs://{bucket}/staging'
  google_cloud_options.temp_location = f'gs://{bucket}/temp'
  google_cloud_options.service_account_email = identity

  pipeline_options.view_as(WorkerOptions).worker_harness_container_image = image
  pipeline_options.view_as(StandardOptions).runner = 'DataflowRunner'
  pipeline_options.view_as(StandardOptions).streaming = 'true'
  pipeline_options.view_as(PortableOptions).environment_type = 'DOCKER'
  pipeline_options.view_as(PortableOptions).environment_config = image
  pipeline_options.view_as(DebugOptions).experiments = ['use_runner_v2']
 
  pipeline_options.view_as(SetupOptions).save_main_session = False

  # The pipeline will be run on exiting the with block.
  with beam.Pipeline(options=pipeline_options) as p:
    # Read the text file[pattern] into a PCollection.
    lines = p | 'Read data' >> ReadFromText(known_args.input)
    lines | 'Process data' >> beam.ParDo(RunCommand())
