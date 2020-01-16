# nepms-zendesk-stats

Automate collection of various zendesk ticket stats and send them to prometheus pushgateway

## Getting Started
1. Clone github repo
```shell script
git clone git@github.com:nepworldwide/nepms-zendesk-stats.git
cd nepms-zendesk-stats
```

### Prerequisites
- Python 3.7 or newer (might work on older 3.x versions)

### Installing

1. Deploy configuration template
```shell script
cp config/config.sample.yml config/config.yml
```
2. Update configuration file `config/config.yml`
3. Build docker image
```shell script
make build
```
4. Run it
```shell script
make run
```

## Deployment

### Docker
See above

### Standalone with python virtual env

1. Create virtual environment and activate it
```shell script
virtualenv venv
source venv/bin/activate
```

2. Install dependencies with pip
```shell script
pip install -r requirements.txt
```

3. Run the script
```shell script
python app/app.py
```

## Configuration

See [config/config.sample.yml](config/config.sample.yml)
All settings must be present as the script will validate the JSON doc created by parsing the yml configuration file.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

