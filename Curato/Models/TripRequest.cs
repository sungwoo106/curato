public class TripRequest
{
    public string Location { get; set; }
    public string Companion { get; set; }
    public int Budget { get; set; }
    public string StartTime { get; set; }
    public List<string> PreferredPlaceTypes { get; set; }
    public (double Latitude, double Longitude) Coordinates { get; set; }
}
