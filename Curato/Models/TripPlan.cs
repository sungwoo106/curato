public class TripPlan
{
    public List<string> SelectedPlaces { get; set; } = new();
    public string EmotionalNarrative { get; set; } = string.Empty;
    public List<PlaceSuggestion> SuggestedPlaces { get; set; } = new();
}
