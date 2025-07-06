class ZoneMerger:
    def __init__(self, zones, threshold=0.002):
        self.zones = zones
        self.threshold = threshold

    def merge(self):
        # Output: Combined zones with metadata (source count, strength, etc.)
        combined_zones = []
        # TODO: Implement merging based on price proximity or overlap
        return combined_zones
    
    def merge_MTF(self):
        merged = []
        used = set()

        for i, zone in enumerate(self.zones):
            if i in used:
                continue

            group = [zone]
            used.add(i)

            z_high = zone['zone_high'] * (1 + self.threshold)
            z_low = zone['zone_low'] * (1 - self.threshold)

            for j, other in enumerate(self.zones):
                if j in used or i == j:
                    continue

                other_high = other['zone_high'] * (1 + self.threshold)
                other_low = other['zone_low'] * (1 - self.threshold)

                # Check if zones overlap
                if (
                    (other_low <= z_high and other_high >= z_high) or
                    (other_high >= z_low and other_low <= z_low) or
                    (other_low >= z_low and other_high <= z_high) or
                    (other_low <= z_low and other_high >= z_high)
                ):
                    group.append(other)
                    used.add(j)

                    # Expand merged zone bounds
                    z_high = max(z_high, other['zone_high'] * (1 + self.threshold))
                    z_low = min(z_low, other['zone_low'] * (1 - self.threshold))

            # Merge metadata
            merged_zone = {
                'zone_high': max(z['zone_high'] for z in group),
                'zone_low': min(z['zone_low'] for z in group),
                'zone_width': max(z['zone_high'] for z in group) - min(z['zone_low'] for z in group),
                'types': list(set(z['type'] for z in group)),
                'timeframes': list(set(z['time_frame'] for z in group)),
                'count': len(group),
                'sources': group
            }

            merged.append(merged_zone)

        return merged

