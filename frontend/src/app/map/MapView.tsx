"use client";

import { useEffect, useRef, useMemo } from "react";
import L from "leaflet";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

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
  venue: string;
  city: string;
  lat: number;
  lng: number;
  date: string;
  date_label: string;
  capacity: number | null;
  price_min: number;
  price_max: number;
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

// Custom marker icons using SVG
function createEventIcon(eventType: string, isSelected: boolean): L.DivIcon {
  const colors: Record<string, { bg: string; border: string }> = {
    concert: { bg: "#6366f1", border: "#4f46e5" },
    festival: { bg: "#f59e0b", border: "#d97706" },
    popup_store: { bg: "#10b981", border: "#059669" },
    brand_event: { bg: "#ec4899", border: "#db2777" },
  };

  const icons: Record<string, string> = {
    concert: `<path d="M9 18V5l12-2v13" stroke="white" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="6" cy="18" r="3" fill="white"/><circle cx="18" cy="16" r="3" fill="white"/>`,
    festival: `<path d="M4 22V4c0-1 1-2 2-2h12c1 0 2 1 2 2v18" stroke="white" stroke-width="2" fill="none"/><path d="M12 2v20" stroke="white" stroke-width="2"/><path d="M4 12h16" stroke="white" stroke-width="2"/>`,
    popup_store: `<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="white" stroke-width="2" fill="none"/><polyline points="9,22 9,12 15,12 15,22" stroke="white" stroke-width="2" fill="none"/>`,
    brand_event: `<polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26" stroke="white" stroke-width="2" fill="none"/>`,
  };

  const c = colors[eventType] || colors.concert;
  const iconSvg = icons[eventType] || icons.concert;
  const size = isSelected ? 42 : 32;
  const ringSize = isSelected ? 50 : 0;

  return L.divIcon({
    className: "custom-event-marker",
    html: `
      <div style="position:relative;width:${size}px;height:${size}px;display:flex;align-items:center;justify-content:center;">
        ${isSelected ? `<div style="position:absolute;inset:-4px;border-radius:50%;border:3px solid ${c.bg};opacity:0.4;animation:ping 1.5s cubic-bezier(0,0,0.2,1) infinite;"></div>` : ""}
        <div style="width:${size}px;height:${size}px;border-radius:50%;background:${c.bg};border:2px solid ${isSelected ? "white" : c.border};display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.3);${isSelected ? "transform:scale(1.1);" : ""}transition:transform 0.2s;">
          <svg width="${size * 0.5}" height="${size * 0.5}" viewBox="0 0 24 24" fill="none">${iconSvg}</svg>
        </div>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
}

// Component to fly to selected event
function FlyToSelected({ event }: { event: ArtistEvent | null }) {
  const map = useMap();

  useEffect(() => {
    if (event) {
      map.flyTo([event.lat, event.lng], 10, { duration: 0.8 });
    }
  }, [event, map]);

  return null;
}

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
  const mapRef = useRef<L.Map | null>(null);

  // Group overlapping events (same lat/lng ± 0.001)
  const markers = useMemo(() => {
    return events.map((event) => ({
      event,
      icon: createEventIcon(
        event.event_type,
        selectedEvent?.id === event.id
      ),
    }));
  }, [events, selectedEvent?.id]);

  return (
    <div className="relative rounded-xl overflow-hidden border shadow-sm">
      <style jsx global>{`
        .custom-event-marker {
          background: transparent !important;
          border: none !important;
        }
        @keyframes ping {
          75%, 100% {
            transform: scale(2);
            opacity: 0;
          }
        }
        .leaflet-popup-content-wrapper {
          border-radius: 12px !important;
          padding: 0 !important;
          overflow: hidden;
        }
        .leaflet-popup-content {
          margin: 0 !important;
          min-width: 200px;
        }
        .leaflet-popup-tip {
          background: white !important;
        }
      `}</style>
      <MapContainer
        center={[46.6, 2.5]}
        zoom={6}
        style={{ height: "600px", width: "100%" }}
        zoomControl={true}
        ref={mapRef}
      >
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        <FlyToSelected event={selectedEvent} />

        {markers.map(({ event, icon }) => (
          <Marker
            key={event.id}
            position={[event.lat, event.lng]}
            icon={icon}
            eventHandlers={{
              click: () => onSelectEvent(event),
            }}
          >
            <Popup>
              <div className="p-3 min-w-[220px]">
                <div className="flex items-center gap-2 mb-2">
                  {event.artist_image ? (
                    <img
                      src={event.artist_image}
                      alt={event.artist_name}
                      className="w-8 h-8 rounded-full object-cover"
                    />
                  ) : (
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center"
                      style={{
                        backgroundColor:
                          eventTypes[event.event_type]?.color || "#6366f1",
                      }}
                    >
                      <span className="text-white text-xs font-bold">
                        {event.artist_name[0]}
                      </span>
                    </div>
                  )}
                  <div>
                    <p className="font-bold text-sm">{event.artist_name}</p>
                    <p className="text-[11px] text-gray-500">
                      {event.event_type_label}
                    </p>
                  </div>
                </div>
                <div className="space-y-1 text-xs">
                  <p className="flex items-center gap-1">
                    <span className="text-gray-400">Lieu:</span>
                    <span className="font-medium">{event.venue}</span>
                  </p>
                  <p className="flex items-center gap-1">
                    <span className="text-gray-400">Date:</span>
                    <span className="font-medium">{event.date_label}</span>
                  </p>
                  <p className="flex items-center gap-1">
                    <span className="text-gray-400">Ville:</span>
                    <span className="font-medium">{event.city}</span>
                  </p>
                  {event.capacity && (
                    <p className="flex items-center gap-1">
                      <span className="text-gray-400">Capacité:</span>
                      <span className="font-medium">
                        {event.capacity.toLocaleString()}
                      </span>
                    </p>
                  )}
                  <p className="flex items-center gap-1">
                    <span className="text-gray-400">Prix:</span>
                    <span className="font-medium">
                      {event.price_min}€ – {event.price_max}€
                    </span>
                  </p>
                  {event.monthly_listeners > 0 && (
                    <p className="flex items-center gap-1">
                      <span className="text-gray-400">Auditeurs:</span>
                      <span className="font-medium">
                        {formatListeners(event.monthly_listeners)}
                      </span>
                    </p>
                  )}
                </div>
                {event.artist_genres.length > 0 && (
                  <div className="flex gap-1 mt-2 flex-wrap">
                    {event.artist_genres.map((g) => (
                      <span
                        key={g}
                        className="inline-block px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-600 text-[10px]"
                      >
                        {g}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Map legend */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-white/95 backdrop-blur-sm rounded-lg p-3 shadow-lg border">
        <p className="text-[10px] font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">
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

      {/* Event count overlay */}
      <div className="absolute top-4 right-4 z-[1000] bg-white/95 backdrop-blur-sm rounded-lg px-3 py-2 shadow-lg border">
        <p className="text-xs font-medium">
          {events.length} événement{events.length !== 1 ? "s" : ""}
        </p>
      </div>
    </div>
  );
}
