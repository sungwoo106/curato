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

                // Debug 1: Confirm method fired
                File.WriteAllText(System.IO.Path.Combine(AppContext.BaseDirectory, "outputpage_loaded.txt"), "OutputPage_Loaded fired");

                // Build JavaScript array from AppState
                var plan = AppState.SharedTripPlan ?? new TripPlan();
                AppState.SharedTripPlan = plan;

                // TEMP: Load mock LLM output from file
                var mockJsonPath = System.IO.Path.Combine(AppContext.BaseDirectory, "Resources", "MockData", "mock_phi_hd_output.json");
                //Debugging
                File.WriteAllText(System.IO.Path.Combine(AppContext.BaseDirectory, "check_json_path.txt"),
                $"Exists: {File.Exists(mockJsonPath)}\nPath: {mockJsonPath}");
                
                if (File.Exists(mockJsonPath))
                {

                    var phiJson = File.ReadAllText(mockJsonPath);
                    var phiPlaces = JsonSerializer.Deserialize<List<PhiPlace>>(phiJson);

                    // Debug 3: Suggestions loaded
                    File.WriteAllText(System.IO.Path.Combine(AppContext.BaseDirectory, "mock_suggestion_debug.txt"),
                    $"Suggestions count: {suggestions?.Count}");

                    if (suggestions != null && suggestions.Any())
                    {
                        plan.SuggestedPlaces = suggestions
                            .Where(p => p.Latitude != 0 && p.Longitude != 0)
                            .ToList();

                        // Debug 4: Final assigned suggestions
                        File.WriteAllText(System.IO.Path.Combine(AppContext.BaseDirectory, "plan_suggestions.txt"),
                        string.Join("\n", plan.SuggestedPlaces.Select(p => $"{p.Name}: {p.Latitude}, {p.Longitude}")));

                        // If no center coordinates were provided, use the first suggestion
                        if (!coords.HasValue && plan.SuggestedPlaces.Count > 0)
                        {
                            lat = plan.SuggestedPlaces[0].Latitude;
                            lng = plan.SuggestedPlaces[0].Longitude;
                        }
                    }

                }

                string coordArray = "["
                    + string.Join(",", plan.SuggestedPlaces
                        .Where(p => p.Latitude != 0 && p.Longitude != 0)
                        .Select(p => $"{{ lat: {p.Latitude}, lng: {p.Longitude} }}"))
                    + "]";

                var finalHtml = htmlTemplate
                    .Replace("{API_KEY}", kakaoMapKey)
                    .Replace("{LAT}", plan.SuggestedPlaces.FirstOrDefault()?.Latitude.ToString(CultureInfo.InvariantCulture) ?? "37.5665")
                    .Replace("{LNG}", plan.SuggestedPlaces.FirstOrDefault()?.Longitude.ToString(CultureInfo.InvariantCulture) ?? "126.9780")
                    .Replace("{COORD_ARRAY}", coordArray);

                // Debug 5: Output final rendered HTML
                File.WriteAllText(Path.Combine(AppContext.BaseDirectory, "final_html_rendered.html"), finalHtml);

                await MapWebView.EnsureCoreWebView2Async();
                MapWebView.NavigateToString(finalHtml);
            }
            catch (Exception ex)
            {
                // Debug 6
                File.WriteAllText(Path.Combine(AppContext.BaseDirectory, "map_debug_error.txt"), ex.ToString());
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


