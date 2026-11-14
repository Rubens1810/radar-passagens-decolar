import os
from datetime import date, timedelta
import httpx


class FlightCollector:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        self.base_url = "https://serpapi.com/search.json"

    def _generate_dates(self, base_date_str: str, flexible_days: int) -> list[str]:
        base = date.fromisoformat(base_date_str)
        return [
            (base + timedelta(days=offset)).isoformat()
            for offset in range(-flexible_days, flexible_days + 1)
        ]

    def resolve_booking_url(self, flight: dict) -> dict:
        dep = flight["dep_airport"]
        arr = flight["arr_airport"]
        dep_date = flight["departure_date"]

        flight["seller"] = "Decolar"
        flight["url"] = (
            f"https://www.decolar.com/shop/flights/results/oneway/"
            f"{dep}/{arr}/{dep_date}/1/0/0"
        )
        return flight
    
        """Busca o link direto da agência/companhia aérea usando o booking_token (só chamado se houver alerta)."""
        token = flight.get("booking_token")
        dep = flight["dep_airport"]
        arr = flight["arr_airport"]
        dep_date = flight["departure_date"]

        # Fallback direto para a página de seleção da Decolar (nunca joga para tela genérica)
        fallback_url = (
            f"https://www.decolar.com/shop/flights/results/oneway/"
            f"{dep}/{arr}/{dep_date}/1/0/0"
        )

        if not token:
            flight["seller"] = "Decolar (Busca Direta)"
            flight["url"] = fallback_url
            return flight

        params = {
            "engine": "google_flights",
            "departure_id": dep,
            "arrival_id": arr,
            "outbound_date": dep_date,
            "type": "2",
            "booking_token": token,
            "currency": "BRL",
            "hl": "pt-br",
            "gl": "br",
            "api_key": self.api_key,
        }

        try:
            response = httpx.get(self.base_url, params=params, timeout=20.0)
            response.raise_for_status()
            data = response.json()

            booking_options = data.get("booking_options", [])
            if booking_options:
                # Pega a opção de reserva mais barata (ex: Decolar, LATAM, GOL)
                best_option = booking_options[0].get("together", {})
                seller = best_option.get("book_with", "Companhia Aérea / Agência")
                booking_req = best_option.get("booking_request", {})
                direct_url = booking_req.get("url")

                if direct_url:
                    flight["seller"] = seller
                    flight["url"] = direct_url
                    return flight
        except Exception as e:
            print(f"⚠️ Não foi possível resolver booking_token, usando link direto Decolar: {e}")

        flight["seller"] = "Decolar (Busca Direta)"
        flight["url"] = fallback_url
        return flight

    def search_trips(self, trips: list[dict]) -> list[dict]:
        if not self.api_key:
            raise ValueError("SERPAPI_KEY não encontrada no arquivo .env")

        results = []

        for trip in trips:
            trip_name = trip["trip_name"]
            origins_str = ",".join(o.upper() for o in trip["origins"])
            destinations_str = ",".join(d.upper() for d in trip["destinations"])
            flexible_days = trip.get("flexible_days", 0)
            target_price = trip.get("target_price")

            dates_to_check = self._generate_dates(trip["departure_date"], flexible_days)
            best_offer_for_trip = None

            for dep_date in dates_to_check:
                print(f"🔎 [{trip_name}] Buscando {origins_str} -> {destinations_str} em {dep_date}...")

                params = {
                    "engine": "google_flights",
                    "departure_id": origins_str,
                    "arrival_id": destinations_str,
                    "outbound_date": dep_date,
                    "type": "2",
                    "currency": "BRL",
                    "hl": "pt-br",
                    "gl": "br",
                    "api_key": self.api_key,
                }

                try:
                    response = httpx.get(self.base_url, params=params, timeout=25.0)
                    response.raise_for_status()
                    data = response.json()

                    all_flights = data.get("best_flights", []) + data.get("other_flights", [])
                    priced_flights = [f for f in all_flights if "price" in f]

                    if not priced_flights:
                        continue

                    cheapest = min(priced_flights, key=lambda x: float(x["price"]))
                    price = float(cheapest["price"])

                    first_leg = cheapest["flights"][0]
                    last_leg = cheapest["flights"][-1]
                    dep_airport = first_leg["departure_airport"]["id"]
                    arr_airport = last_leg["arrival_airport"]["id"]
                    airline = first_leg.get("airline", "Companhia não informada")

                    candidate = {
                        "trip_name": trip_name,
                        "dep_airport": dep_airport,
                        "arr_airport": arr_airport,
                        "route": f"{dep_airport} -> {arr_airport}",
                        "departure_date": dep_date,
                        "airline": airline,
                        "price": price,
                        "target_price": float(target_price) if target_price is not None else None,
                        "currency": "BRL",
                        "booking_token": cheapest.get("booking_token"),
                        "seller": "Companhia / Agência",
                        "url": "",
                    }

                    if best_offer_for_trip is None or candidate["price"] < best_offer_for_trip["price"]:
                        best_offer_for_trip = candidate

                except httpx.HTTPStatusError as e:
                    print(f"⚠️ Erro HTTP na API ({dep_date}): {e.response.text}")
                except Exception as e:
                    print(f"⚠️ Erro inesperado ({dep_date}): {e}")

            if best_offer_for_trip:
                results.append(best_offer_for_trip)
            else:
                print(f"⚠️ Nenhuma oferta encontrada para {trip_name}.")

        return results