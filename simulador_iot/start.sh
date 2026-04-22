#!/bin/bash

# Arrancar el productor de sensores en segundo plano
python -u sensor_producer.py &

# Arrancar el productor de cámara (este se queda en primer plano)
python -u camara_producer.py