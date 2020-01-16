import argparse
import yaml
import logging
import os
import sys
import time

from schema import Schema, SchemaError
import requests
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from apscheduler.schedulers.background import BlockingScheduler


class Config(object):
    def __init__(self):
        # Set up config path
        self.config_data = None
        self.config_file = os.path.dirname(os.path.realpath(__file__)) + "/config/config.yml"

    def load(self, check=True):
        with open(self.config_file, 'r') as stream:
            try:
                self.config_data = yaml.safe_load(stream)
            except yaml.YAMLError as e:
                print('Configuration file can not be parsed. Error: {e}')
        if check:
            self.check()
        return self.config_data

    def check(self):
        # Expected model of the schema of the config
        config_schema = Schema({
            'pushgateway': {
                'host': str,
                'job': {
                    'zendesk-ticket-count': {
                        'interval': int
                    }
                }
            },
            'zendesk-ticket-count': {
                'base_url': str,
                'search_api': str,
                'zendesk_api_user': str,
                'zendesk_api_token': str,
                'filter': {
                    'status': list,
                    'tag': list
                }
            }
        })
        try:
            config_schema.validate(self.config_data)
        except SchemaError as e:
            logging.error(f'Configuration schema is not valid. {e}')
            sys.exit()
        else:
            logging.debug('Configuration schema is valid')


class ZendeskApi(object):
    def __init__(self, zendesk_config):
        self.api_url = zendesk_config['base_url'] + zendesk_config['search_api']
        self.user = zendesk_config['zendesk_api_user']
        self.token = zendesk_config['zendesk_api_token']
        self.filter = zendesk_config['filter']

    def get(self, params):
        logging.info(f'GET "{self.api_url}" with params "{params}"')
        response = requests.get(self.api_url, params=params, auth=(self.user + "/token", self.token))
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logging.error(f'Response HTTP code - "{response.status_code}". Content - {e.response.content}')
        else:
            logging.info(f"API responded in {response.elapsed.total_seconds()} seconds")
            return response.json()

    def load(self):
        data = {}
        for tag in self.filter['tag']:
            data.update({tag: {}})
            for status in self.filter['status']:
                request_data = self.get({'query': f'type:ticket tags:{tag} status:{status}'})
                data[tag].update({status: request_data['count']})
        return data


class Pushgateway(object):
    def __init__(self, host, job_name, data):
        # init registry
        self.registry = CollectorRegistry()
        self.pushgateway_host = host
        self.job_name = job_name
        self.ticket_status_g = Gauge(
            "zendesk_tickets_status",
            "Zendesk ticket status",
            ["tag", "status"],
            registry=self.registry,
        )
        for tag in data:
            for status in data[tag]:
                self.ticket_status_g.labels(tag=tag, status=status).set(data[tag][status])

    def push(self):
        try:
            logging.info(f'Sending data to Prometheus host: "{self.pushgateway_host}", job - "{self.job_name}"')
            push_start_time = time.time()
            push_to_gateway(self.pushgateway_host, job=self.job_name, registry=self.registry)
            push_end_time = time.time()
            push_duration = push_end_time - push_start_time
            logging.info(f"Successfully sent data to Prometheus. Time taken - {push_duration} seconds")
        except Exception as e:
            logging.error(f"Failed to send data to Prometheus. Msg - {e}")


def log_level_switch(log_level):
    return dict(error=logging.ERROR, info=logging.INFO, debug=logging.DEBUG)[log_level]


def zendesk_ticket_count(config_data):
    logging.info('Job has been started')
    start = time.time()
    zendesk_ticket_count_data = ZendeskApi(config_data['zendesk-ticket-count']).load()
    Pushgateway(config_data['pushgateway']['host'], 'zendesk-ticket-count', zendesk_ticket_count_data).push()
    logging.info(f"Job has finished in {time.time() - start} seconds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prometheus collector for zendesk ticket status based on tag"
    )

    parser.add_argument(
        "-l",
        "--log-level",
        type=str,
        required=False,
        default="info",
        help="default info [error, info, debug]",
    )

    args = parser.parse_args()
    logging.basicConfig(level=log_level_switch(args.log_level))

    logging.info("Loading configuration")
    config_data = Config().load()
    logging.info("Configuration has been loaded successfully")

    # init scheduler
    scheduler = BlockingScheduler()

    # configure scheduler
    # zendesk-ticket-count
    schedule_id = 'zendesk-ticket-count'
    schedule_name = 'zendesk-ticket-count'
    schedule_interval = config_data['pushgateway']['job'][schedule_name]['interval']
    logging.info(f'Scheduling "{schedule_id}", will be run every {schedule_interval} seconds')
    scheduler.add_job(
        zendesk_ticket_count,
        'interval',
        [config_data],
        seconds=schedule_interval,
        id='schedule_id',
    )

    # start scheduler
    scheduler.start()

