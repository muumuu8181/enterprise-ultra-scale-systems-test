import asyncio
import json
import logging
import asyncio_mqtt as mqtt
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import AsyncSessionLocal
from src.models.city_models import SensorReading, Sensor

logger = logging.getLogger(__name__)

class MQTTGateway:
    """
    MQTTゲートウェイクラス: センサーデータの受信とコマンド送信を行う
    """
    def __init__(self, broker_host: str = "localhost", port: int = 1883):
        self.broker_host = broker_host
        self.port = port
        self.client = None

    async def connect(self):
        """
        ブローカーに接続し、処理を開始する
        """
        try:
            async with mqtt.Client(self.broker_host, self.port) as client:
                self.client = client
                await self.subscribe_sensors()

                async with client.messages() as messages:
                    async for message in messages:
                        await self.process_message(message)
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")

    async def subscribe_sensors(self):
        """
        全センサーのトピックを購読する
        """
        if self.client:
            await self.client.subscribe("sensors/+/readings")
            logger.info("Subscribed to sensors/+/readings")

    async def process_message(self, message):
        """
        メッセージを解析し、データベースに保存する
        """
        try:
            topic = message.topic
            payload = message.payload.decode()
            data = json.loads(payload)

            # トピックからsensor_idを取得 (例: sensors/123/readings)
            sensor_id = int(topic.split("/")[1])

            async with AsyncSessionLocal() as session:
                reading = SensorReading(
                    sensor_id=sensor_id,
                    value=data.get("value"),
                    unit=data.get("unit"),
                    quality_score=data.get("quality_score", 1.0)
                )
                session.add(reading)
                await session.commit()
                logger.info(f"Saved reading for sensor {sensor_id}")

        except Exception as e:
            logger.error(f"Failed to process message: {e}")

    async def publish_command(self, sensor_id: int, command: dict):
        """
        センサーにコマンドを送信する
        """
        if self.client:
            topic = f"sensors/{sensor_id}/commands"
            payload = json.dumps(command)
            await self.client.publish(topic, payload)
            logger.info(f"Published command to {topic}")
