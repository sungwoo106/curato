using System.Text.Json.Serialization;

public class PhiPlace
{
    [JsonPropertyName("place_name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("latitude")]
    public double Latitude { get; set; }

    [JsonPropertyName("longitude")]
    public double Longitude { get; set; }
}
