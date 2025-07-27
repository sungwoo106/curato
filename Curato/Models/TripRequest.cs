using System.Text.Json.Serialization;

public class TripRequest
{
    [JsonPropertyName("location_query")]
    public string Location { get; set; }

    [JsonPropertyName("companion_type")]
    public string Companion { get; set; }

    [JsonPropertyName("budget")]
    public string Budget { get; set; }

    [JsonPropertyName("starting_time")]
    public string StartTime { get; set; }

    [JsonPropertyName("categories")]
    public List<string> PreferredPlaceTypes { get; set; }
}
