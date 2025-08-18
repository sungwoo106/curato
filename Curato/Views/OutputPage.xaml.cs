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
            
            // Debug: Log the plan data
            System.Diagnostics.Debug.WriteLine($"OutputPage constructor - Plan: {plan?.EmotionalNarrative}");
            System.Diagnostics.Debug.WriteLine($"OutputPage constructor - Plan is null: {plan == null}");
            System.Diagnostics.Debug.WriteLine($"OutputPage constructor - EmotionalNarrative is null/empty: {string.IsNullOrWhiteSpace(plan?.EmotionalNarrative)}");

            // Set the preferences summary
            PreferencesSummaryLabel.Text = AppState.SharedInputViewModel.PreferencesSummary;

            if (plan != null && !string.IsNullOrWhiteSpace(plan.EmotionalNarrative))
            {
                System.Diagnostics.Debug.WriteLine($"Setting EmotionalItineraryTextBlock with text: {plan.EmotionalNarrative}");
                EmotionalItineraryTextBlock.Inlines.Clear();
                foreach (var para in plan.EmotionalNarrative.Split(new[] { "\n", "\r\n" }, StringSplitOptions.RemoveEmptyEntries))
                {
                    EmotionalItineraryTextBlock.Inlines.Add(new Run(para.Trim()));
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                }
            }
            else
            {
                System.Diagnostics.Debug.WriteLine("Plan or EmotionalNarrative is null/empty, not setting text");
                EmotionalItineraryTextBlock.Text = "No story generated. Please try again.";
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
                string? location = AppState.SharedInputViewModel?.LocationQuery?.ToLowerInvariant();

                string selectedMockFile = location switch
                {
                    string s when s.Contains("hongdae") || s.Contains("홍대") => "mock_phi_hd_output.json",
                    string s when s.Contains("gangnam") || s.Contains("강남") => "mock_phi_gn_output.json",
                    string s when s.Contains("itaewon") || s.Contains("이태원") => "mock_phi_it_output.json",
                    string s when s.Contains("seongsu") || s.Contains("성수") => "mock_phi_ss_output.json",
                    string s when s.Contains("bukchon") || s.Contains("북촌") => "mock_phi_bc_output.json",
                    _ => "mock_phi_hd_output.json" // fallback
                };

                var mockJsonPath = System.IO.Path.Combine(AppContext.BaseDirectory, "Resources", "MockData", selectedMockFile);

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


