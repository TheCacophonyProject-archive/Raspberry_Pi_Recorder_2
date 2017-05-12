# Raspberry_Pi_Recorder_2

## License
This project is licensed under the GPL-V3

### Licence disclaimer
The Cacophony Project will, upon request, consider making code in this
repository available under the MIT license if doing so maximises our
impact for the benefit of NZ's native ecosystems. We will not do this
lightly.

We ask that open source contributors, who will hold copyright over
significant project contributions, alert us if they find this
possibility unacceptable. To minimise complexities in contribution, we
will endeavour to seek permission of contributors we can easily contact
before altering the license to MIT, however if we are unable to contact
contributors readily, we will assume consent.

## Setup
`sudo apt-get update`
`sudo apt-get install gpac libav-tools python-opencv python-numpy`

Install pylepton, used for thermal camera.
`git clone https://github.com/groupgets/pylepton.git`  
`cd pylepton/`  
`sudo python setup.py install`

Enable camera, SPI, I2C, and change Timezone on the Raspberry Pi.

Clone config file and set params.   
`cd Raspberry_Pi_Recorder_2`    
`cp config_TEMPLATE.json config.json`
`chmod +x main.py`

Run main.py to start app.

## Start on reboot
This will start a screen session running the app on reboot.

`sudo apt-get install screen`
`crontab -e`
Add this task to cron
`@reboot /usr/bin/screen -dmS ThermalRecorder /home/pi/Raspberry_Pi_Recorder_2/main.py`
