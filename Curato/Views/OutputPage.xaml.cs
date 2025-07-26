using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Globalization;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using Curato.Models;
using secure;

namespace Curato.Views
{
    public partial class OutputPage : UserControl
    {
        public double Latitude { get; set; }
        public double Longitude { get; set; }

        public OutputPage()
        {
            InitializeComponent();
            this.DataContext = AppState.SharedTripPlan;
            this.Loaded += OutputPage_Loaded;

            // Load the emotional narrative into the TextBlock
            var plan = AppState.SharedTripPlan;

            // Set the preferences summary
            PreferencesSummaryLabel.Text = AppState.SharedInputViewModel.PreferencesSummary;

            if (plan != null && !string.IsNullOrWhiteSpace(plan.EmotionalNarrative))
            {
                EmotionalItineraryTextBlock.Inlines.Clear();
                foreach (var para in plan.EmotionalNarrative.Split(new[] { "\n", "\r\n" }, StringSplitOptions.RemoveEmptyEntries))
                {
                    EmotionalItineraryTextBlock.Inlines.Add(new Run(para.Trim()));
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                }
            }
        }

        private async void OutputPage_Loaded(object sender, RoutedEventArgs e)
        {
            try
            {
                double lat = 37.5665; // default to Seoul
                double lng = 126.9780;

                var coords = AppState.SharedInputViewModel.SelectedLocationCoordinates;
                if (coords.HasValue)
                {
                    lat = coords.Value.Latitude;
                    lng = coords.Value.Longitude;
                }

                var mockJsonPath = Path.Combine(AppContext.BaseDirectory, "mock_phi_hd_output.json");

                // 🔍 Confirm file presence and path
                File.WriteAllText("check_json_path.txt", $"Exists: {File.Exists(mockJsonPath)}\nPath: {mockJsonPath}");

                if (File.Exists(mockJsonPath))
                {
                    var json = File.ReadAllText(mockJsonPath);
                    var suggestions = JsonSerializer.Deserialize<List<PlaceSuggestion>>(json);

                    if (suggestions != null && suggestions.Any())
                    {
                        var plan = AppState.SharedTripPlan;
                        plan.SuggestedPlaces = suggestions
                            .Where(p => p.Latitude != 0 && p.Longitude != 0)
                            .Select(p => new PlaceSuggestion
                            {
                                Name = p.Name,
                                Latitude = p.Latitude,
                                Longitude = p.Longitude
                            }).ToList();
                    }
                }

                var debugLogPath = Path.Combine(AppContext.BaseDirectory, "map_marker_debug.txt");
                var debugPlan = AppState.SharedTripPlan;
                if (debugPlan?.SuggestedPlaces == null)
                {
                    File.WriteAllText(debugLogPath, "SuggestedPlaces is null.");
                }
                else if (!debugPlan.SuggestedPlaces.Any())
                {
                    File.WriteAllText(debugLogPath, "SuggestedPlaces exists but is empty.");
                }
                else
                {
                    var lines = debugPlan.SuggestedPlaces
                        .Select(p => $"{p.Name} - lat: {p.Latitude}, lng: {p.Longitude}")
                        .ToList();

                    File.WriteAllLines(debugLogPath, lines);
                }

                string coordArray = "[]";
                if (debugPlan?.SuggestedPlaces != null)
                {
                    var points = debugPlan.SuggestedPlaces
                        .Where(p => p.Latitude != 0 && p.Longitude != 0)
                        .Select(p => $"{{ lat: {p.Latitude.ToString(CultureInfo.InvariantCulture)}, lng: {p.Longitude.ToString(CultureInfo.InvariantCulture)} }}");

                    coordArray = "[" + string.Join(",", points) + "]";
                }

                string html = File.ReadAllText(htmlPath)
                    .Replace("{API_KEY}", kakaoMapKey)
                    .Replace("{LAT}", lat.ToString(CultureInfo.InvariantCulture))
                    .Replace("{LNG}", lng.ToString(CultureInfo.InvariantCulture))
                    .Replace("{COORD_ARRAY}", coordArray);

                await MapWebView.EnsureCoreWebView2Async();
                MapWebView.NavigateToString(html);
            }
            catch (Exception ex)
            {
                File.WriteAllText("map_debug_error.txt", ex.ToString());
            }
        }
    }
}