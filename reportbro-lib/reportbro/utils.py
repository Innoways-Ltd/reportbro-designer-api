import datetime
import decimal

current_datetime_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')


def get_int_value(data, key):
    value = data.get(key)
    return int(value) if value else 0


def get_float_value(data, key):
    value = data.get(key)
    if value:
        if isinstance(value, (float, int)):
            return float(value)
        if isinstance(value, str):
            return float(value.replace(',', '.'))
    return 0.0


def get_str_value(data, key):
    value = data.get(key)
    if isinstance(value, str):
        return value
    return ''


def to_string(val):
    if not isinstance(val, str):
        return str(val)
    return val


def parse_datetime_string(val):
    # Handle ISO 8601 format with timezone (e.g., 2025-12-26T14:30:00+08:00 or 2025-12-26T15:07:19Z)
    if 'T' in val:
        # Replace 'T' with space for standard parsing
        val_normalized = val.replace('T', ' ')
        
        # Handle 'Z' timezone (UTC)
        if val_normalized.endswith('Z'):
            val_normalized = val_normalized[:-1]
            colon_count = val_normalized.count(':')
            # Check for milliseconds/microseconds
            has_decimal = '.' in val_normalized
            if colon_count == 1:
                date_format = '%Y-%m-%d %H:%M.%f' if has_decimal else '%Y-%m-%d %H:%M'
            elif colon_count == 2:
                date_format = '%Y-%m-%d %H:%M:%S.%f' if has_decimal else '%Y-%m-%d %H:%M:%S'
            else:
                date_format = '%Y-%m-%d'
            return datetime.datetime.strptime(val_normalized, date_format)
        
        # Handle timezone offset (e.g., +08:00 or -05:00)
        if '+' in val_normalized or val_normalized.count('-') > 2:
            # Find timezone part
            tz_sep_idx = max(val_normalized.rfind('+'), val_normalized.rfind('-', 10))  # start search after date part
            if tz_sep_idx > 0:
                # Remove timezone offset for now (simple approach)
                val_normalized = val_normalized[:tz_sep_idx].strip()
        
        colon_count = val_normalized.count(':')
        # Check for milliseconds/microseconds
        has_decimal = '.' in val_normalized
        if colon_count == 1:
            date_format = '%Y-%m-%d %H:%M.%f' if has_decimal else '%Y-%m-%d %H:%M'
        elif colon_count == 2:
            date_format = '%Y-%m-%d %H:%M:%S.%f' if has_decimal else '%Y-%m-%d %H:%M:%S'
        else:
            date_format = '%Y-%m-%d'
        return datetime.datetime.strptime(val_normalized, date_format)
    
    # Standard format without 'T' separator
    date_format = '%Y-%m-%d'
    colon_count = val.count(':')
    if colon_count == 1:
        date_format = '%Y-%m-%d %H:%M'
    elif colon_count == 2:
        date_format = '%Y-%m-%d %H:%M:%S'
    return datetime.datetime.strptime(val, date_format)


def parse_number_string(val):
    return decimal.Decimal(val.replace(',', '.'))


# return image size so image fits into configured width/height and keep aspect ratio
def get_image_display_size(width, height, image_width, image_height):
    if image_width <= width and image_height <= height:
        image_display_width, image_display_height = image_width, image_height
    else:
        size_ratio = image_width / image_height
        tmp = width / size_ratio
        if tmp <= height:
            image_display_width = width
            image_display_height = tmp
        else:
            image_display_width = height * size_ratio
            image_display_height = height
    return image_display_width, image_display_height
