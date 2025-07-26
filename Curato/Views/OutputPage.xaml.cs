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

            double lat = 37.5665; // default to Seoul
            double lng = 126.9780;

            var coords = AppState.SharedInputViewModel.SelectedLocationCoordinates;
            if (coords.HasValue)
            {
                lat = coords.Value.Latitude;
                lng = coords.Value.Longitude;
            }

            try
            {
                var htmlPath = System.IO.Path.Combine(AppContext.BaseDirectory, "Resources", "html", "map_template.html");
                var htmlTemplate = File.ReadAllText(htmlPath);
                var kakaoMapKey = crypto_utils.get_kakao_map_api_key();

                // Build JavaScript array from AppState
                var JSplan = AppState.SharedTripPlan ?? new TripPlan();
                AppState.SharedTripPlan = JSplan;

                // TEMP: Load mock LLM output from file
                string location = AppState.SharedInputViewModel?.StartLocation?.ToLowerInvariant() ?? "";

                var locationSuffixes = new Dictionary<string, string>
                {
                    { "홍대", "hd" }, { "hongdae", "hd" },
                    { "강남", "gn" }, { "gangnam", "gn" },
                    { "북촌", "bc" }, { "bukchon", "bc" },
                    { "이태원", "it" }, { "itaewon", "it" },
                    { "신사", "ss" }, { "sinsa", "ss" }
                };

                string suffix = "hd";  // fallback
                if (location != null)
                {
                    foreach (var kvp in locationSuffixes)
                    {
                        if (location.Contains(kvp.Key))
                        {
                            suffix = kvp.Value;
                            break;
                        }
                    }
                }

                var mockJsonPath = Path.Combine(AppContext.BaseDirectory, "Resources", "MockData", $"mock_phi_{suffix}_output.json");
                File.WriteAllText(Path.Combine(AppContext.BaseDirectory, "mock_json_debug.txt"),
                    $"Search query: {location}\nSuffix used: {suffix}\nPath: {mockJsonPath}");

                if (File.Exists(mockJsonPath))
                {
                    var phiJson = File.ReadAllText(mockJsonPath);
                    var phiPlaces = JsonSerializer.Deserialize<List<PhiPlace>>(phiJson);

                    if (phiPlaces != null && phiPlaces.Any())
                    {
                        JSplan.SuggestedPlaces = phiPlaces
                            .Where(p => p.Latitude != 0 && p.Longitude != 0)
                            .ToList();

                        if (!coords.HasValue && JSplan.SuggestedPlaces.Count > 0)
                        {
                            lat = JSplan.SuggestedPlaces[0].Latitude;
                            lng = JSplan.SuggestedPlaces[0].Longitude;
                        }
                    }
                }


                string coordArray = "["
                    + string.Join(",", JSplan.SuggestedPlaces
                        .Where(p => p.Latitude != 0 && p.Longitude != 0)
                        .Select((p, i) =>
                            $"{{ lat: {p.Latitude.ToString(CultureInfo.InvariantCulture)}, lng: {p.Longitude.ToString(CultureInfo.InvariantCulture)}, name: \"{p.Name.Replace("\"", "\\\"")}\", index: {i + 1} }}"))
                    + "]";

                var finalHtml = htmlTemplate
                    .Replace("{API_KEY}", kakaoMapKey)
                    .Replace("{LAT}", JSplan.SuggestedPlaces.FirstOrDefault()?.Latitude.ToString(CultureInfo.InvariantCulture) ?? "37.5665")
                    .Replace("{LNG}", JSplan.SuggestedPlaces.FirstOrDefault()?.Longitude.ToString(CultureInfo.InvariantCulture) ?? "126.9780")
                    .Replace("{COORD_ARRAY}", coordArray);

                await MapWebView.EnsureCoreWebView2Async();
                MapWebView.NavigateToString(finalHtml);
            }
            catch (Exception ex)
            {

            }
        }

        private void EditButton_Click(object sender, RoutedEventArgs e)
        {
            var mainWindow = Window.GetWindow(this) as MainWindow;
            if (mainWindow != null)
            {
                mainWindow.MainFrame.Content = new SearchPage();
            }
        }
    }
}


