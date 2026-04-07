"use client";

import { useEffect, useRef, useCallback } from "react";
import {
  Map,
  MapMarker,
  MarkerContent,
  MarkerPopup,
  MarkerTooltip,
  MapControls,
  type MapRef,
} from "@/components/ui/map";

interface ArtistEvent {
  id: string;
  artist_name: string;
  artist_id: string;
  artist_image: string | null;
  artist_score: number;
  artist_genres: string[];
  monthly_listeners: number;
  event_type: "concert" | "festival" | "popup_store" | "brand_event";
  event_type_label: string;
  event_name?: string;
  event_url?: string;
  event_image?: string;
  venue: string;
  city: string;
  country?: string;
  lat: number;
  lng: number;
  date: string;
  date_label: string;
  capacity: number | null;
  price_min: number;
  price_max: number;
  currency?: string;
  status?: string;
  promoter?: string;
  source?: string;
}

interface EventTypeConfig {
  label: string;
  color: string;
  bgColor: string;
}

interface MapViewProps {
  events: ArtistEvent[];
  selectedEvent: ArtistEvent | null;
  onSelectEvent: (event: ArtistEvent) => void;
  eventTypes: Record<string, EventTypeConfig>;
}

const EVENT_COLORS: Record<string, string> = {
  concert: "#6366f1",
  festival: "#f59e0b",
  popup_store: "#10b981",
  brand_event: "#ec4899",
};

const EVENT_ICONS: Record<string, string> = {
  concert: "🎵",
  festival: "🎪",
  popup_store: "🏪",
  brand_event: "⭐",
};

function formatListeners(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

export default function MapView({
  events,
  selectedEvent,
  onSelectEvent,
  eventTypes,
}: MapViewProps) {
  const mapRef = useRef<MapRef>(null);

  // Fly to selected event
  useEffect(() => {
    if (!mapRef.current || !selectedEvent) return;
    mapRef.current.flyTo({
      center: [selectedEvent.lng, selectedEvent.lat],
      zoom: 10,
      duration: 800,
    });
  }, [selectedEvent]);

  return (
    <div className="relative rounded-xl overflow-hidden border shadow-sm" style={{ height: 600 }}>
      <Map
        ref={mapRef}
        center={[2.5, 46.6]}
        zoom={5}
        pitch={45}
        className="h-full w-full"
      >
        {events.map((event) => {
          const isSelected = selectedEvent?.id === event.id;
          const color = EVENT_COLORS[event.event_type] || "#6366f1";
          const icon = EVENT_ICONS[event.event_type] || "📍";

          return (
            <MapMarker
              key={event.id}
              longitude={event.lng}
              latitude={event.lat}
              onClick={() => onSelectEvent(event)}
            >
              <MarkerContent>
                <div
                  className="flex items-center justify-center rounded-full border-2 shadow-lg transition-all duration-200"
                  style={{
                    width: isSelected ? 40 : 30,
                    height: isSelected ? 40 : 30,
                    backgroundColor: color,
                    borderColor: isSelected ? "white" : color,
                    transform: isSelected ? "scale(1.15)" : "scale(1)",
                  }}
                >
                  <span style={{ fontSize: isSelected ? 18 : 14 }}>{icon}</span>
                </div>
                {isSelected && (
                  <div
                    className="absolute inset-0 rounded-full animate-ping"
                    style={{
                      backgroundColor: color,
                      opacity: 0.3,
                      width: isSelected ? 40 : 30,
                      height: isSelected ? 40 : 30,
                    }}
                  />
                )}
              </MarkerContent>

              <MarkerTooltip>
                <div className="font-medium">{event.artist_name}</div>
                <div className="text-[10px] opacity-70">{event.event_type_label} · {event.city}</div>
              </MarkerTooltip>

              <MarkerPopup className="w-[260px] p-0">
                <div className="p-3">
                  <div className="flex items-center gap-2 mb-2">
                    {event.artist_image ? (
                      <img
                        src={event.artist_image}
                        alt={event.artist_name}
                        className="w-9 h-9 rounded-full object-cover"
                      />
                    ) : (
                      <div
                        className="w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-bold"
                        style={{ backgroundColor: color }}
                      >
                        {event.artist_name[0]}
                      </div>
                    )}
                    <div className="min-w-0">
                      <p className="font-bold text-sm truncate">{event.artist_name}</p>
                      <p className="text-[11px] text-muted-foreground" style={{ color }}>
                        {event.event_type_label}
                      </p>
                    </div>
                  </div>

                  <div className="space-y-1 text-xs text-muted-foreground">
                    {event.event_name && event.event_name !== event.artist_name && (
                      <p className="font-medium text-foreground">{event.event_name}</p>
                    )}
                    <p>📍 {event.venue}, {event.city}</p>
                    <p>📅 {event.date_label}</p>
                    {(event.price_min || event.price_max) && (
                      <p>💰 {event.price_min ?? "?"}€ – {event.price_max ?? "?"}€</p>
                    )}
                    {event.capacity && (
                      <p>👥 {event.capacity.toLocaleString()} places</p>
                    )}
                    {event.monthly_listeners > 0 && (
                      <p>🎧 {formatListeners(event.monthly_listeners)} auditeurs</p>
                    )}
                    {event.promoter && (
                      <p>🏢 {event.promoter}</p>
                    )}
                  </div>

                  {event.event_url && (
                    <a
                      href={event.event_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block mt-2 text-center text-[11px] font-semibold py-1.5 rounded-md text-white transition-opacity hover:opacity-90"
                      style={{ backgroundColor: color }}
                    >
                      🎫 Voir / Acheter
                    </a>
                  )}

                  {event.artist_genres.length > 0 && (
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {event.artist_genres.slice(0, 3).map((g) => (
                        <span
                          key={g}
                          className="inline-block px-1.5 py-0.5 rounded-full text-[10px] font-medium"
                          style={{
                            backgroundColor: `${color}15`,
                            color: color,
                          }}
                        >
                          {g}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </MarkerPopup>
            </MapMarker>
          );
        })}

        <MapControls
          position="bottom-right"
          showZoom
          showCompass
          showLocate
          showFullscreen
        />
      </Map>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-background/95 backdrop-blur-sm rounded-lg p-3 shadow-lg border">
        <p className="text-[10px] font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider">
          Légende
        </p>
        <div className="space-y-1">
          {Object.entries(eventTypes).map(([key, config]) => (
            <div key={key} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: config.color }}
              />
              <span className="text-[11px]">{config.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Event count */}
      <div className="absolute top-4 right-4 z-[1000] bg-background/95 backdrop-blur-sm rounded-lg px-3 py-2 shadow-lg border">
        <p className="text-xs font-medium">
          🗺️ {events.length} événement{events.length !== 1 ? "s" : ""}
        </p>
      </div>
    </div>
  );
}
