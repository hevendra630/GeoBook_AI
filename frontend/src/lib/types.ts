export type ClientLocation = {
  latitude: number;
  longitude: number;
};

export type PlaceResult = {
  source: "osm" | "db";
  name: string;
  address: string;
  rating?: number | null;
  distance_meters?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  phone?: string | null;
  maps_url?: string | null;
  business_id?: string | null;
};

export type BookingConfirmation = {
  appointment_id: string;
  business_id: string;
  start_at: string;
  end_at: string;
};

export type ChatResponse = {
  intent: "search" | "book" | "unknown" | string;
  normalized_location?: ClientLocation | null;
  results: PlaceResult[];
  booking?: BookingConfirmation | null;
  assistant_message: string;
  session_id?: string | null;
};

