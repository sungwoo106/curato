using System.Text.Json.Serialization;

namespace Curato.Models
{
    public class PlaceSuggestion
    {
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("latitude")]
    public double Latitude { get; set; }

    [JsonPropertyName("longitude")]
    public double Longitude { get; set; }
    }
}