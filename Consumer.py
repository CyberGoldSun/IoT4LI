import cv2
from typing import Final
from confluent_kafka import DeserializingConsumer
from confluent_kafka.serialization import IntegerDeserializer
import numpy as np

applicationID: Final[str] = "CovertChannel"
bootstrapServers: Final[str] = "localhost:9092,localhost:9093"
topic_list = ['channel']

consumer_properties = {
    'client.id': applicationID,
    'bootstrap.servers': bootstrapServers,
    'group.id': 'invoice-consumer-group',
    'key.deserializer': IntegerDeserializer()
}
consumer = DeserializingConsumer(consumer_properties)
consumer.subscribe(topic_list)

cv2.namedWindow("Video", cv2.WINDOW_AUTOSIZE)

while True:
    messages = consumer.poll(100)
    frame_bytes = messages.value()
    frame = cv2.imdecode(np.frombuffer(frame_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)

    cv2.imshow("Video", frame)
    cv2.waitKey(1)
