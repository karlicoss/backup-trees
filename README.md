This script gets filesystem trees for the specified directories and uploads them on Yandex.Disk.

Intended use is adding it as a Cron job, e.g twice a day, so in case you lose you HDD you will at least have the list of your files.

# Configuring
    
    cp config.py.sample config.py
    
Then, acquire the Yandex.Disk token and fill items to back up.

# Running
  
    backup-trees.py
    

# Prerequisites

* notification daemon, supporting actions
* `pynotify2`
