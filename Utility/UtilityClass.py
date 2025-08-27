class UtilityFunctions():
    def merge_lists_by_key(self,old_list, new_list, key="id"):
        # Convert old list to dict keyed by primary key
        merged = {d[key]: d for d in old_list}

        for new_item in new_list:
            pk = new_item[key]
            if pk in merged:
                # Update existing entry with new values
                merged[pk].update(new_item)
            else:
                # Insert new entry
                merged[pk] = new_item

        # Return back as list
        return list(merged.values())
    
    def remove_data_from_lists_by_key(self, data_list,to_remove, key ):
        """
        Remove items from a list of dictionaries where the specified key matches the given value.
        """
        result = []
        for item in data_list:
            if item[key] not in to_remove:
                result.append(item)
        return result
    
    def getDHMS(self,timestring:str = '1D-1h-1m-1s'):
        #get day,hour,minutes,seconds from string
        times = timestring.split('-')
        codes = ['D','h','m','s']
        result = {'D': 0, 'h': 0, 'm': 0, 's': 0}
        for part in times:
            for code in codes:
                if part.endswith(code):
                    try:
                        result[code] = int(part[:-1])
                    except ValueError:
                        result[code] = 0
                    break
        
        return result['D'], result['h'], result['m'], result['s']
