from kafka import KafkaConsumer
from google.cloud import bigquery
import json
import traceback
import re
import os
import utils
import datetime
import time
import logging
from kafka import TopicPartition , OffsetAndMetadata

logging.basicConfig(filename ='app.log',
                        level = logging.INFO, 
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
logger=logging.getLogger(__name__)

config_data = utils.read_config('config.json')
config_data=config_data.get(os.environ["environment"])
kafka_topic = config_data.get('kafka').get('TOPIC')
kafka_servers = config_data.get('kafka').get('BOOT_STRAP')
google_service_account = config_data.get('google_cred_path')

try:
    #created kafka consumer
    consumer = KafkaConsumer(
        kafka_topic,
        bootstrap_servers=kafka_servers,
        api_version=(0,11,5),
        group_id="gp1",
        auto_offset_reset='earliest',  # Choose 'latest' or 'earliest'
        enable_auto_commit=False,
        value_deserializer=lambda x: x.decode('utf-8')
    )
    #create connection with bquery
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]= google_service_account
    client = bigquery.Client()

    Bquery_insert_record = list()
    bquery_dataset_id = config_data.get("bquery_dataset_id")
    bquery_table_id = config_data.get("bquery_table_id")
    table_ref = client.dataset(bquery_dataset_id).table(bquery_table_id)
    bad_comment_pattern = r'%s'%config_data.get("bad_comment_regex")
    table_columns = config_data.get("table_columns")
    logger.info("created kafka consumer and connected to big query")
    print("created kafka consumer and connected to big query")

except Exception as err:
    logger.error(err)
    traceback.print_exc()

try:
    print("streaming started")
    while True:
        messages = None
        try:
            messages = consumer.poll(timeout_ms=100)
            print("read kafka data")
            Bquery_insert_record = list()
            tp_topic,om = None,None
            if not messages:
                print("No new messages")
            else:
                for tp, tp_messages in messages.items():
                    #transform the incoming json to wide format 
                    for message in tp_messages:
                        record = json.loads(message.value)
                        if record.get("glid"):
                            record["GLID"]= record.get("glid")
                        if record.get("GLID") and record.get("event_timestamp") and record.get("event_name"):
                            record["event_timestamp"] = record["event_timestamp"].replace("am","").replace("pm","")
                            try:
                                record.update({"event_date":datetime.datetime.strptime(record["event_timestamp"], '%d-%m-%Y %H:%M:%S').strftime("%Y-%m-%d")})
                                record["event_timestamp"] = datetime.datetime.strptime(record["event_timestamp"], '%d-%m-%Y %H:%M:%S').strftime("%Y-%m-%d %H:%M:%S")
                            except:
                                record.update({"event_date":datetime.datetime.strptime(record["event_timestamp"], '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d")})
                            record["GLID"] = float(record["GLID"])
                            record = dict([(key,value) for key,value in record.items() if key in table_columns])
                            record.update({"insertion_time":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                            if record.get("event_name") == "glusr_rating":
                                if record.get('comment') and re.match(r"%s"%(bad_comment_pattern),record.get('comment').lower()):
                                    record.update({"bad_rating_comment":int(1)})
                                    Bquery_insert_record.append(record)  
                            elif record.get("event_name") =="glusr_suspect_tagging" and record.get('hrs_tag'):
                                hrs_tag = record.get("hrs_tag")
                                record.update({record.get("event_name"):1})
                                Bquery_insert_record.append(record) 
                            else:
                                record.update({record.get("event_name"):int(1)})
                                Bquery_insert_record.append(record) 
                        tp_topic=TopicPartition(message.topic,message.partition)
                        om = OffsetAndMetadata(message.offset+1, message.timestamp)
                    print("transformed data")
        except Exception as err:
            print(err)
            traceback.print_exc()
            application_log = {"response":"500","message":"data transformation failed","err":str(err),"TAG":"application_log","application":"kafka_consumer"}
            print(json.dumps(application_log))
        if Bquery_insert_record:
            print(Bquery_insert_record)
            errors = client.insert_rows_json(table_ref, Bquery_insert_record)
            if len(errors) > 0:
                with open("errors_insert_records.json","a") as f:
                    json.dump(Bquery_insert_record,f)
                for error in errors:
                    print(error)
                application_log = {"response":"500","message":"failed to insert","data_len":len(Bquery_insert_record),"offset":om.offset,"topic":tp_topic.topic,"TAG":"application_log","application":"kafka_consumer"}
                print(json.dumps(application_log))
            else:
                logger.info(f"data pushed till {om}")
                consumer.commit({tp_topic:om})
                application_log = {"response":"200","message":"data inserted","data_len":len(Bquery_insert_record),"offset":om.offset,"topic":tp_topic.topic,"TAG":"application_log","application":"kafka_consumer"}
                print(json.dumps(application_log))

        time.sleep(60)
except KeyboardInterrupt:
    # Handle keyboard interrupt (Ctrl+C)
    consumer.close()
except Exception as err:
    logger.error(err)
    print(err)
    traceback.print_exc()








