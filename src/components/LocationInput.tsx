import React, { useEffect, useState } from 'react';
import {
    ActivityIndicator,
    Pressable,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    View,
} from 'react-native';
import { colors } from '../utils/colors';

interface LocationResult {
  name: string;
  latitude: number;
  longitude: number;
  type?: string;
  category?: string;
  landmark?: string;
  display_name?: string;
  similarity?: number;
  source?: 'local' | 'osm' | 'mapmyindia';
}

interface LocationInputProps {
  label: string;
  placeholder?: string;
  onSelect: (location: LocationResult) => void;
  currentValue?: string;
}

export default function LocationInput({
  label,
  placeholder = 'Search location...',
  onSelect,
  currentValue = '',
}: LocationInputProps) {
  const [query, setQuery] = useState(currentValue);
  const [results, setResults] = useState<LocationResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [typing, setTyping] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<LocationResult | null>(null);
  const [showResults, setShowResults] = useState(false);

  // Search locations from backend
  const searchLocations = async (searchQuery: string) => {
    if (searchQuery.length < 3) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      // Adjust IP as needed
      const API_URL = 'http://192.168.2.6:8000'; // Update with your IP
      
      const response = await fetch(`${API_URL}/api/v1/rides/search-location`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery }),
      });

      if (response.ok) {
        const data = await response.json();
        // Use the new 'results' field which already has exclusive fallback ranking applied
        const results = data.results || [];
        
        // Results already have 'source' field from backend
        // Just need to add display badges and limit to 8
        const displayResults = results.slice(0, 8).map((r: LocationResult) => ({
          ...r,
          // Ensure source field exists (for badge display)
          source: r.source || 'local',
        }));

        setResults(displayResults);
        setShowResults(true);
      }
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // Debounce search with 700ms delay (respects API limits)
  useEffect(() => {
    // Don't search if we just selected a location
    if (selectedLocation) {
      return;
    }

    // Show typing state immediately for queries >= 3 chars
    if (query.length >= 3) {
      setTyping(true);
    } else {
      setTyping(false);
    }

    const timer = setTimeout(() => {
      setTyping(false);
      if (query.length >= 3) {
        searchLocations(query);
      } else {
        setResults([]);
        setShowResults(false);
      }
    }, 700); // 700ms debounce (respects MapmyIndia rate limits)

    return () => clearTimeout(timer);
  }, [query, selectedLocation]);

  const handleSelectLocation = (location: LocationResult) => {
    setShowResults(false); // Hide results first
    setResults([]); // Clear results
    setSelectedLocation(location); // Mark as selected
    setQuery(location.name); // Update query (won't trigger search due to selectedLocation)
    onSelect(location); // Notify parent
  };

  const handleInputFocus = () => {
    // Only show results if we have a query and results, but not if we just selected something
    if (query.length >= 3 && results.length > 0 && !selectedLocation) {
      setShowResults(true);
    }
  };

  const handleInputChange = (text: string) => {
    setQuery(text);
    setSelectedLocation(null); // Clear selection when typing
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>

      <View style={styles.inputWrapper}>
        <TextInput
          placeholder={placeholder}
          value={query}
          onChangeText={handleInputChange}
          onFocus={handleInputFocus}
          style={styles.input}
          placeholderTextColor="#999"
        />
        {typing && !loading && (
          <Text style={styles.typingIndicator}>✍️</Text>
        )}
        {loading && <ActivityIndicator color={colors.primary} style={styles.loader} />}
      </View>

      {/* Show selected location details */}
      {selectedLocation && (
        <View style={styles.selectedCard}>
          {selectedLocation.landmark && (
            <Text style={styles.selectedLandmark}>🏛️ {selectedLocation.landmark}</Text>
          )}
          <Text style={styles.selectedCoords}>
            📍 {selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)}
          </Text>
        </View>
      )}

      {showResults && results.length > 0 && (
        <ScrollView 
          style={styles.resultsList} 
          scrollEnabled={true}
          nestedScrollEnabled={true}
          keyboardShouldPersistTaps="handled"
        >
          {results.map((result, index) => (
            <Pressable
              key={`${result.latitude}-${result.longitude}-${index}`}
              onPress={() => handleSelectLocation(result)}
              style={({ pressed }) => [
                styles.resultItem,
                pressed && styles.resultItemPressed,
              ]}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            >
              <View style={styles.resultContent}>
                <View style={styles.resultHeader}>
                  <Text style={styles.resultName}>{result.name}</Text>
                  {result.source && (
                    <Text style={[
                      styles.sourceBadge,
                      result.source === 'local' && styles.sourceBadgeLocal,
                      result.source === 'osm' && styles.sourceBadgeOSM,
                      result.source === 'mapmyindia' && styles.sourceBadgeMapmyIndia,
                    ]}>
                      {result.source === 'local' ? '📍' : result.source === 'osm' ? '🗺️' : '🇮🇳'}
                    </Text>
                  )}
                </View>
                {result.landmark && (
                  <Text style={styles.resultSubtitle}>{result.landmark}</Text>
                )}
                {result.category && (
                  <Text style={styles.resultCategory}>{result.category}</Text>
                )}
                <Text style={styles.resultCoords}>
                  {result.latitude.toFixed(4)}, {result.longitude.toFixed(4)}
                </Text>
              </View>
              {result.similarity && (
                <Text style={styles.similarity}>{Math.round(result.similarity * 100)}%</Text>
              )}
            </Pressable>
          ))}
        </ScrollView>
      )}

      {showResults && results.length === 0 && query.length >= 3 && !loading && !typing && (
        <View style={styles.noResults}>
          <Text style={styles.noResultsText}>No locations found</Text>
        </View>
      )}
      {query.length > 0 && query.length < 3 && !selectedLocation && (
        <View style={styles.minCharsHint}>
          <Text style={styles.minCharsText}>Type at least 3 characters to search</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
    color: colors.secondary,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: colors.primary,
    borderRadius: 8,
    paddingHorizontal: 12,
    backgroundColor: '#fff',
  },
  input: {
    flex: 1,
    paddingVertical: 10,
    fontSize: 14,
    color: colors.secondary,
  },
  loader: {
    marginLeft: 8,
  },
  typingIndicator: {
    marginLeft: 8,
    fontSize: 16,
  },
  resultsList: {
    maxHeight: 250,
    marginTop: 8,
    borderWidth: 1,
    borderColor: colors.primary,
    borderRadius: 8,
    backgroundColor: '#fff',
  },
  resultItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  resultContent: {
    flex: 1,
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  resultItemPressed: {
    backgroundColor: '#fff9e6',
  },
  resultName: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.secondary,
    marginBottom: 2,
  },
  resultSubtitle: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  resultCategory: {
    fontSize: 11,
    color: colors.primary,
    fontWeight: '500',
    marginBottom: 2,
  },
  resultCoords: {
    fontSize: 10,
    color: '#999',
  },
  similarity: {
    fontSize: 12,
    fontWeight: 'bold',
    color: colors.primary,
    marginLeft: 12,
  },
  noResults: {
    marginTop: 8,
    paddingVertical: 16,
    paddingHorizontal: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
  },
  noResultsText: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  selectedCard: {
    backgroundColor: '#f0f8ff',
    borderRadius: 6,
    padding: 8,
    marginTop: 6,
    borderLeftWidth: 3,
    borderLeftColor: colors.primary,
  },
  selectedLandmark: {
    fontSize: 12,
    color: '#555',
    marginBottom: 2,
  },
  selectedCoords: {
    fontSize: 11,
    color: '#999',
    fontFamily: 'monospace',
  },
  sourceBadge: {
    fontSize: 14,
    paddingHorizontal: 4,
    paddingVertical: 2,
  },
  sourceBadgeLocal: {
    // Green for local database
  },
  sourceBadgeOSM: {
    // Blue for OpenStreetMap
  },
  sourceBadgeMapmyIndia: {
    // Orange for MapmyIndia
  },
  minCharsHint: {
    marginTop: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#fff9e6',
    borderRadius: 6,
    borderLeftWidth: 3,
    borderLeftColor: colors.primary,
  },
  minCharsText: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
});
