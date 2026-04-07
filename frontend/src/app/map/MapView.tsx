"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import Globe from "react-globe.gl";

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

const EVENT_COLORS: Record<string, string> = {
  concert: "#6366f1",
  festival: "#f59e0b",
  popup_store: "#10b981",
  brand_event: "#ec4899",
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
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const globeRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(800);

  // Measure container width
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const update = () => setWidth(el.clientWidth);
    update();
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setWidth(entry.contentRect.width);
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Initial camera: center on France
  const handleGlobeReady = useCallback(() => {
    const globe = globeRef.current;
    if (!globe) return;
    globe.pointOfView({ lat: 46.6, lng: 2.5, altitude: 1.8 }, 0);
    const controls = globe.controls();
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.3;
    controls.enableZoom = true;
  }, []);

  // Fly to selected event
  useEffect(() => {
    const globe = globeRef.current;
    if (!globe || !selectedEvent) return;
    globe.controls().autoRotate = false;
    globe.pointOfView(
      { lat: selectedEvent.lat, lng: selectedEvent.lng, altitude: 0.5 },
      800
    );
  }, [selectedEvent]);

  const ringsData = selectedEvent ? [selectedEvent] : [];

  return (
    <div
      ref={containerRef}
      className="relative rounded-xl overflow-hidden border border-white/10 shadow-lg"
      style={{
        height: 600,
        background:
          "radial-gradient(ellipse at center, #0a0a2e 0%, #000010 100%)",
      }}
    >
      <Globe
        ref={globeRef}
        width={width}
        height={600}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
        bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
        backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
        atmosphereColor="#6366f1"
        atmosphereAltitude={0.18}
        // Points
        pointsData={events}
        pointLat="lat"
        pointLng="lng"
        pointColor={(d: object) =>
          EVENT_COLORS[(d as ArtistEvent).event_type] || "#6366f1"
        }
        pointAltitude={(d: object) =>
          selectedEvent?.id === (d as ArtistEvent).id ? 0.06 : 0.01
        }
        pointRadius={(d: object) =>
          selectedEvent?.id === (d as ArtistEvent).id ? 0.45 : 0.2
        }
        pointLabel={(d: object) => {
          const e = d as ArtistEvent;
          const color = EVENT_COLORS[e.event_type] || "#6366f1";
          return `
            <div style="background:rgba(10,10,30,0.92);color:#e2e8f0;padding:10px 14px;border-radius:10px;font-family:system-ui;font-size:12px;border:1px solid ${color}40;backdrop-filter:blur(12px);max-width:250px;pointer-events:none;">
              <div style="font-weight:700;font-size:14px;color:white;margin-bottom:2px;">${e.artist_name}</div>
              <div style="color:${color};font-size:11px;font-weight:600;margin-bottom:6px;">${e.event_type_label}</div>
              <div style="line-height:1.7;font-size:11px;">
                <span style="opacity:0.5;">📍</span> ${e.venue}, ${e.city}<br/>
                <span style="opacity:0.5;">📅</span> ${e.date_label}<br/>
                <span style="opacity:0.5;">💰</span> ${e.price_min}€ – ${e.price_max}€
                ${e.monthly_listeners > 0 ? `<br/><span style="opacity:0.5;">🎧</span> ${formatListeners(e.monthly_listeners)} auditeurs` : ""}
              </div>
              ${
                e.artist_genres.length > 0
                  ? `<div style="margin-top:6px;display:flex;gap:4px;flex-wrap:wrap;">${e.artist_genres
                      .slice(0, 3)
                      .map(
                        (g) =>
                          `<span style="background:${color}25;color:${color};padding:2px 8px;border-radius:10px;font-size:10px;">${g}</span>`
                      )
                      .join("")}</div>`
                  : ""
              }
            </div>
          `;
        }}
        onPointClick={(point: object) => onSelectEvent(point as ArtistEvent)}
        // Pulsing rings around selected event
        ringsData={ringsData}
        ringLat="lat"
        ringLng="lng"
        ringColor={() => (t: number) =>
          `rgba(99,102,241,${Math.sqrt(1 - t)})`
        }
        ringMaxRadius={4}
        ringPropagationSpeed={3}
        ringRepeatPeriod={800}
        onGlobeReady={handleGlobeReady}
        animateIn={true}
      />

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-black/50 backdrop-blur-md rounded-lg p-3 shadow-lg border border-white/10">
        <p className="text-[10px] font-semibold text-white/50 mb-1.5 uppercase tracking-wider">
          Légende
        </p>
        <div className="space-y-1">
          {Object.entries(eventTypes).map(([key, config]) => (
            <div key={key} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full shadow-sm"
                style={{ backgroundColor: config.color }}
              />
              <span className="text-[11px] text-white/80">{config.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Event count */}
      <div className="absolute top-4 right-4 z-10 bg-black/50 backdrop-blur-md rounded-lg px-3 py-2 shadow-lg border border-white/10">
        <p className="text-xs font-medium text-white/90">
          🌍 {events.length} événement{events.length !== 1 ? "s" : ""}
        </p>
      </div>
    </div>
  );
}
