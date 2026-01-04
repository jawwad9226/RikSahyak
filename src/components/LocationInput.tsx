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
  const [selectedLocation, setSelectedLocation] = useState<LocationResult | null>(null);
  const [showResults, setShowResults] = useState(false);

  // Search locations from backend
  const searchLocations = async (searchQuery: string) => {
    if (searchQuery.length < 2) {
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
        // Combine all results and remove duplicates
        const allResults = [
          ...data.exact_matches,
          ...data.fuzzy_matches,
          ...data.nominatim_results,
        ];
        
        // Remove duplicates based on coordinates
        const uniqueResults = allResults.reduce(
          (acc: LocationResult[], curr) => {
            const isDuplicate = acc.some(
              (r) => r.latitude === curr.latitude && r.longitude === curr.longitude
            );
            if (!isDuplicate) {
              acc.push(curr);
            }
            return acc;
          },
          []
        );

        setResults(uniqueResults.slice(0, 8)); // Limit to 8 results
        setShowResults(true);
      }
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // Debounce search
  useEffect(() => {
    // Don't search if we just selected a location
    if (selectedLocation) {
      return;
    }

    const timer = setTimeout(() => {
      if (query.length > 1) {
        searchLocations(query);
      } else {
        setResults([]);
        setShowResults(false);
      }
    }, 300); // 300ms delay

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
    if (query.length > 1 && results.length > 0 && !selectedLocation) {
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
              <View>
                <Text style={styles.resultName}>{result.name}</Text>
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

      {showResults && results.length === 0 && query.length > 1 && !loading && (
        <View style={styles.noResults}>
          <Text style={styles.noResultsText}>No locations found</Text>
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
});
