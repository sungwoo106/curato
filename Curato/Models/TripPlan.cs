using Curato.Models;

public class TripPlan
{
    public List<string> SelectedPlaces { get; set; } = new();
    public string EmotionalNarrative { get; set; } = string.Empty;
    public List<PhiPlace> SuggestedPlaces { get; set; } = new();
}
