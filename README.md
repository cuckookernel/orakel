# orakel

Some experiments in microprediction, muid mining, etc.


See
[www.microprediction.com](www.microprediction.com)


## key_server

A minimalistic middleman between the miner that produces keys and stream publishers / crawlers that use keys. 

After installing the requirements ( `pip install -r  requirements.txt` ) just start it with  `key_server/start_server.sh`

## miner

A miner written in Kotlin, using Bloom filters in an attempt to speed up checking whether a hash is memorable.

On a core i7 (single core) it is able to go through rougly 2 MM hashes per second.


