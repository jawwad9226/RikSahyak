import React from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { colors } from '../utils/colors';

// Conditionally import MapView based on platform
let MapView: any = null;
let Marker: any = null;
let Polyline: any = null;
let UrlTile: any = null;

if (Platform.OS !== 'web') {
  try {
    const Maps = require('react-native-maps');
    MapView = Maps.MapView;
    Marker = Maps.Marker;
    Polyline = Maps.Polyline;
    UrlTile = Maps.UrlTile;
  } catch (error) {
    console.warn('react-native-maps not available');
  }
}

interface MapLocation {
  latitude: number;
  longitude: number;
  name: string;
  description?: string;
}

interface LocationMapProps {
  pickup?: MapLocation;
  dropoff?: MapLocation;
  currentLocation?: MapLocation;
  onLocationPress?: (coordinate: { latitude: number; longitude: number }) => void;
  showDistance?: boolean;
  distance?: number;
  onClose?: () => void;
}

export default function LocationMap({
  pickup,
  dropoff,
  currentLocation,
  onLocationPress,
  showDistance = false,
  distance,
  onClose,
}: LocationMapProps) {
  // Web fallback
  if (Platform.OS === 'web' || !MapView) {
    return (
      <View style={styles.webContainer}>
        <View style={styles.webHeader}>
          <Text style={styles.webTitle}>Map View</Text>
          {onClose && (
            <Pressable style={styles.closeButton} onPress={onClose}>
              <Text style={styles.closeText}>✕</Text>
            </Pressable>
          )}
        </View>

        <View style={styles.webMapPlaceholder}>
          <Text style={styles.placeholderText}>🗺️ Map Preview</Text>

          {pickup && (
            <View style={styles.locationInfo}>
              <Text style={styles.locationLabel}>📍 Pickup:</Text>
              <Text style={styles.locationName}>{pickup.name}</Text>
              <Text style={styles.coordinates}>
                {pickup.latitude.toFixed(4)}, {pickup.longitude.toFixed(4)}
              </Text>
            </View>
          )}

          {dropoff && (
            <View style={styles.locationInfo}>
              <Text style={styles.locationLabel}>🎯 Dropoff:</Text>
              <Text style={styles.locationName}>{dropoff.name}</Text>
              <Text style={styles.coordinates}>
                {dropoff.latitude.toFixed(4)}, {dropoff.longitude.toFixed(4)}
              </Text>
            </View>
          )}

          {showDistance && distance && (
            <View style={styles.distanceInfo}>
              <Text style={styles.distanceText}>📏 Distance: {distance.toFixed(1)} km</Text>
            </View>
          )}
        </View>

        <View style={styles.webFooter}>
          <Text style={styles.webNote}>
            Map functionality available on mobile devices
          </Text>
        </View>
      </View>
    );
  }

  // Calculate map region to fit both markers
  const getRegion = () => {
    if (pickup && dropoff) {
      const minLat = Math.min(pickup.latitude, dropoff.latitude);
      const maxLat = Math.max(pickup.latitude, dropoff.latitude);
      const minLon = Math.min(pickup.longitude, dropoff.longitude);
      const maxLon = Math.max(pickup.longitude, dropoff.longitude);

      return {
        latitude: (minLat + maxLat) / 2,
        longitude: (minLon + maxLon) / 2,
        latitudeDelta: (maxLat - minLat) * 1.5,
        longitudeDelta: (maxLon - minLon) * 1.5,
      };
    }

    if (pickup) {
      return {
        latitude: pickup.latitude,
        longitude: pickup.longitude,
        latitudeDelta: 0.015,
        longitudeDelta: 0.015,
      };
    }

    if (currentLocation) {
      return {
        latitude: currentLocation.latitude,
        longitude: currentLocation.longitude,
        latitudeDelta: 0.015,
        longitudeDelta: 0.015,
      };
    }

    // Default to Malkapur
    return {
      latitude: 20.887,
      longitude: 76.205,
      latitudeDelta: 0.05,
      longitudeDelta: 0.05,
    };
  };

  return (
    <View style={styles.container}>
      <MapView style={styles.map} initialRegion={getRegion()}>
        {/* OpenStreetMap tiles (no API key) */}
        <UrlTile
          urlTemplate="https://c.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maximumZ={19}
          tileSize={256}
          zIndex={-1}
        />
        {/* Current Location Marker */}
        {currentLocation && (
          <Marker
            coordinate={{
              latitude: currentLocation.latitude,
              longitude: currentLocation.longitude,
            }}
            title={currentLocation.name}
            description={currentLocation.description}
            pinColor="#0000ff"
          />
        )}

        {/* Pickup Marker */}
        {pickup && (
          <Marker
            coordinate={{
              latitude: pickup.latitude,
              longitude: pickup.longitude,
            }}
            title="Pickup"
            description={pickup.name}
            pinColor={colors.primary}
            onPress={() =>
              onLocationPress?.({
                latitude: pickup.latitude,
                longitude: pickup.longitude,
              })
            }
          />
        )}

        {/* Dropoff Marker */}
        {dropoff && (
          <Marker
            coordinate={{
              latitude: dropoff.latitude,
              longitude: dropoff.longitude,
            }}
            title="Dropoff"
            description={dropoff.name}
            pinColor={colors.secondary}
            onPress={() =>
              onLocationPress?.({
                latitude: dropoff.latitude,
                longitude: dropoff.longitude,
              })
            }
          />
        )}

        {/* Route Line */}
        {pickup && dropoff && (
          <Polyline
            coordinates={[
              {
                latitude: pickup.latitude,
                longitude: pickup.longitude,
              },
              {
                latitude: dropoff.latitude,
                longitude: dropoff.longitude,
              },
            ]}
            strokeColor={colors.primary}
            strokeWidth={3}
          />
        )}
      </MapView>

      {/* Distance Info Card */}
      {showDistance && distance && (
        <View style={styles.infoCard}>
          <Text style={styles.distanceLabel}>Distance</Text>
          <Text style={styles.distanceValue}>{distance.toFixed(1)} km</Text>
        </View>
      )}

      {/* Close Button */}
      {onClose && (
        <Pressable style={styles.closeButton} onPress={onClose}>
          <Text style={styles.closeButtonText}>✕</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    position: 'relative',
  },
  map: {
    flex: 1,
  },
  infoCard: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    backgroundColor: colors.primary,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  distanceLabel: {
    fontSize: 12,
    color: colors.secondary,
    fontWeight: '500',
  },
  distanceValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.secondary,
  },
  closeButton: {
    position: 'absolute',
    top: 16,
    right: 16,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.secondary,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  closeButtonText: {
    fontSize: 20,
    color: colors.primary,
    fontWeight: 'bold',
  },
  // Web-specific styles
  webContainer: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  webHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: colors.primary,
  },
  webTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.secondary,
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.secondary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeText: {
    fontSize: 16,
    color: colors.primary,
    fontWeight: 'bold',
  },
  webMapPlaceholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#e0e0e0',
    margin: 16,
    borderRadius: 8,
    padding: 20,
  },
  placeholderText: {
    fontSize: 24,
    marginBottom: 20,
  },
  locationInfo: {
    backgroundColor: 'white',
    padding: 12,
    borderRadius: 8,
    marginBottom: 10,
    width: '100%',
    maxWidth: 300,
  },
  locationLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: colors.primary,
    marginBottom: 4,
  },
  locationName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  coordinates: {
    fontSize: 12,
    color: '#666',
  },
  distanceInfo: {
    backgroundColor: colors.primary,
    padding: 12,
    borderRadius: 8,
    marginTop: 10,
  },
  distanceText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.secondary,
    textAlign: 'center',
  },
  webFooter: {
    padding: 16,
    alignItems: 'center',
  },
  webNote: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
});
