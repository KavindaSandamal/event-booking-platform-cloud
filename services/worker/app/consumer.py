import asyncio
import aio_pika
import os
import json
from sqlalchemy import create_engine, text
from datetime import datetime, timezone

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        body = message.body.decode()
        data = json.loads(body)
        booking_id = data.get("booking_id")
        user_id = data.get("user_id")
        # simulate payment & confirmation
        print(f"[Worker] Processing booking {booking_id} for user {user_id}")
        # For demo: just mark booking as confirmed
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE bookings SET status = 'confirmed' WHERE id = :booking_id"),
                {"booking_id": booking_id}
            )
        # Simulate sending notification (print)
        print(f"[Worker] Booking {booking_id} confirmed and notification sent at {datetime.now(timezone.utc).isoformat()}")

async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue("booking_queue", durable=True)
        await queue.consume(process_message, no_ack=False)
        print("[Worker] Awaiting messages...")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
