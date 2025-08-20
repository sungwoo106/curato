using System.Text.Json.Serialization;

namespace Curato.Models
{
    public class TripRequest
    {
        [JsonPropertyName("location_query")]
        public string Location { get; set; } = string.Empty;

        [JsonPropertyName("companion_type")]
        public string Companion { get; set; } = string.Empty;

        [JsonPropertyName("budget")]
        public string Budget { get; set; } = string.Empty;

        [JsonPropertyName("starting_time")]
        public string StartTime { get; set; } = string.Empty;

        [JsonPropertyName("categories")]
        public List<string> PreferredPlaceTypes { get; set; } = new List<string>();
    }
}
