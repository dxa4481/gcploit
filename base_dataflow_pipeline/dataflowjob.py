from __future__ import absolute_import

import argparse
import logging
import re

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
         

def start_job(project, name, bucket, image):
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--input',
      dest='input',
      default='gs://gcploit_eater/startup.sh',
      help='Input file to process.')
  parser.add_argument(
      '--output',
      dest='output',
      default='gs://gcploit_eater/output.txt',
      help='Output file to write results to.')
  parser.add_argument(
      '--extra_package',
      dest='extra_package',
      default='./a_package')
  known_args, pipeline_args = parser.parse_known_args(argv)

  pipeline_options = PipelineOptions(pipeline_args)
  google_cloud_options = pipeline_options.view_as(GoogleCloudOptions)
  google_cloud_options.project = project
  google_cloud_options.job_name = name
  google_cloud_options.region = 'us-east1'
  google_cloud_options.staging_location = f'gs://{bucket}/staging'
  google_cloud_options.temp_location = f'gs://{bucket}/temp'

  pipeline_options.view_as(WorkerOptions).worker_harness_container_image = 'us.gcr.io/speedy-cab-288518/funimage:1.6'
  pipeline_options.view_as(StandardOptions).runner = 'DataflowRunner'
  pipeline_options.view_as(StandardOptions).streaming = 'true'
  pipeline_options.view_as(PortableOptions).environment_type = 'DOCKER'
  pipeline_options.view_as(PortableOptions).environment_config = 'us.gcr.io/speedy-cab-288518/funimage:1.6'
  pipeline_options.view_as(DebugOptions).experiments = ['use_runner_v2']
 
  pipeline_options.view_as(SetupOptions).save_main_session = True

  # The pipeline will be run on exiting the with block.
  with beam.Pipeline(options=pipeline_options) as p:
    # Read the text file[pattern] into a PCollection.
    lines = p | 'Read data' >> ReadFromText(known_args.input)
    lines | 'Process data' >> beam.ParDo(RunCommand())

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  start_job()
