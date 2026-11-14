import json
from pathlib import Path
from dotenv import load_dotenv
from src.collector import FlightCollector
from src.notifier import send_discord_alert
from src.repository import PriceRepository

load_dotenv()


def evaluate_alert(flight: dict, stats: dict) -> tuple[bool, bool]:
    current_price = flight["price"]
    target_price = flight.get("target_price")
    hit_target = bool(target_price is not None and current_price <= target_price)

    # 1ª vez que consultamos esta viagem: sempre alerta (destacando se já bateu o alvo)
    if stats["count"] == 0 or stats["last_notified_price"] is None:
        return True, hit_target

    # Nas próximas vezes, só alerta se o preço CAIU em relação ao último alerta
    if current_price < stats["last_notified_price"]:
        return True, hit_target

    # Ou se caiu pelo menos 5% abaixo da média histórica (e ainda não foi alertado nesse valor)
    if stats["avg_price"] and current_price <= (stats["avg_price"] * 0.95) and current_price != stats["last_notified_price"]:
        return True, hit_target

    return False, False
    current_price = flight["price"]
    target_price = flight.get("target_price")
    hit_target = bool(target_price is not None and current_price <= target_price)

    if hit_target:
        return True, True

    if stats["count"] == 0 or stats["last_notified_price"] is None:
        return True, False

    if current_price < stats["last_notified_price"]:
        return True, False

    if stats["avg_price"] and current_price <= (stats["avg_price"] * 0.95):
        return True, False

    return False, False


def run():
    routes_path = Path("src/routes.json")
    with open(routes_path, "r", encoding="utf-8") as f:
        trips = json.load(f)

    collector = FlightCollector()
    repo = PriceRepository()
    flights = collector.search_trips(trips)

    for flight in flights:
        stats = repo.get_stats(flight["trip_name"])
        notify, hit_target = evaluate_alert(flight, stats)

        if notify:
            flight = collector.resolve_booking_url(flight)
            print(
                f"🚨 Alerta [{flight['trip_name']}]: {flight['route']} em {flight['departure_date']} "
                f"por R$ {flight['price']:.2f} via {flight['seller']}"
            )
            send_discord_alert(flight, avg_price=stats["avg_price"], hit_target=hit_target)
            print("📨 Notificação enviada para o Discord!")
        else:
            print(
                f"💤 Sem queda relevante para {flight['trip_name']} "
                f"(Atual: R$ {flight['price']:.2f} | Último alerta: R$ {stats['last_notified_price']:.2f})"
            )

        repo.save_price(flight, notified=notify)


if __name__ == "__main__":
    run()