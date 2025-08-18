using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Globalization;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using Curato.Models;
using secure;
using Curato.Helpers;

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

            // Set the preferences summary
            PreferencesSummaryLabel.Text = AppState.SharedInputViewModel.PreferencesSummary;
        }

        private async void OutputPage_Loaded(object sender, RoutedEventArgs e)
        {
            // Wait a moment for the AppState to be properly populated
            await Task.Delay(100);
            
            // Load the emotional narrative into the TextBlock
            var plan = AppState.SharedTripPlan;
            
            // Log the plan data
            Logger.LogInfo($"OutputPage_Loaded - Plan: {plan?.EmotionalNarrative}");
            Logger.LogInfo($"OutputPage_Loaded - Plan is null: {plan == null}");
            Logger.LogInfo($"OutputPage_Loaded - EmotionalNarrative is null/empty: {string.IsNullOrWhiteSpace(plan?.EmotionalNarrative)}");
            Logger.LogInfo($"OutputPage_Loaded - SuggestedPlaces count: {plan?.SuggestedPlaces?.Count ?? 0}");
            
            if (plan?.SuggestedPlaces != null && plan.SuggestedPlaces.Any())
            {
                Logger.LogInfo($"OutputPage_Loaded - First place: {plan.SuggestedPlaces[0].Name} at ({plan.SuggestedPlaces[0].Latitude}, {plan.SuggestedPlaces[0].Longitude})");
            }

            if (plan != null && !string.IsNullOrWhiteSpace(plan.EmotionalNarrative))
            {
                Logger.LogInfo($"Setting EmotionalItineraryTextBlock with text: {plan.EmotionalNarrative}");
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
                Logger.LogInfo("Plan or EmotionalNarrative is null/empty, not setting text");
                EmotionalItineraryTextBlock.Text = "No story generated. Please try again.";
                
                // Try to reload from AppState after a longer delay
                await Task.Delay(1000);
                var retryPlan = AppState.SharedTripPlan;
                if (retryPlan != null && !string.IsNullOrWhiteSpace(retryPlan.EmotionalNarrative))
                {
                    Logger.LogInfo($"Retry successful - setting text: {retryPlan.EmotionalNarrative}");
                    EmotionalItineraryTextBlock.Inlines.Clear();
                    foreach (var para in retryPlan.EmotionalNarrative.Split(new[] { "\n", "\r\n" }, StringSplitOptions.RemoveEmptyEntries))
                    {
                        EmotionalItineraryTextBlock.Inlines.Add(new Run(para.Trim()));
                        EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                        EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                    }
                }
            }

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

                // Get the plan from AppState
                var JSplan = AppState.SharedTripPlan ?? new TripPlan();
                
                // Use the actual suggested places from the generated plan
                if (JSplan.SuggestedPlaces != null && JSplan.SuggestedPlaces.Count > 0)
                {
                    Logger.LogInfo($"Using {JSplan.SuggestedPlaces.Count} suggested places from generated plan");
                    
                    // Find the first valid coordinate set
                    var firstValidPlace = JSplan.SuggestedPlaces.FirstOrDefault(p => 
                        p.Latitude != 0 && p.Longitude != 0 && 
                        p.Latitude >= 33.0 && p.Latitude <= 38.5 &&  // Valid Korea latitude range
                        p.Longitude >= 124.0 && p.Longitude <= 132.0); // Valid Korea longitude range
                    
                    if (firstValidPlace != null)
                    {
                        // Use the first valid place for map center
                        lat = firstValidPlace.Latitude;
                        lng = firstValidPlace.Longitude;
                        Logger.LogInfo($"Using first valid place coordinates: lat={lat}, lng={lng}");
                    }
                    else
                    {
                        Logger.LogWarning("No valid coordinates found in suggested places, using default Seoul coordinates");
                        lat = 37.5665; // Seoul
                        lng = 126.9780;
                    }
                }
                else
                {
                    Logger.LogInfo("No suggested places in plan, using default Seoul coordinates");
                }

                string coordArray = "[]"; // Default empty array
                
                if (JSplan.SuggestedPlaces != null && JSplan.SuggestedPlaces.Any())
                {
                    // Filter out invalid coordinates and create the array
                    var validPlaces = JSplan.SuggestedPlaces.Where(p => 
                        p.Latitude != 0 && p.Longitude != 0 && 
                        p.Latitude >= 33.0 && p.Latitude <= 38.5 &&  // Valid Korea latitude range
                        p.Longitude >= 124.0 && p.Longitude <= 132.0).ToList(); // Valid Korea longitude range
                    
                    if (validPlaces.Any())
                    {
                        coordArray = "["
                            + string.Join(",", validPlaces
                                .Select((p, i) =>
                                    $"{{ lat: {p.Latitude.ToString(CultureInfo.InvariantCulture)}, lng: {p.Longitude.ToString(CultureInfo.InvariantCulture)}, name: \"{p.Name.Replace("\"", "\\\"")}\", index: {i + 1} }}"))
                            + "]";
                        
                        Logger.LogInfo($"Generated coordinate array with {validPlaces.Count} valid coordinates");
                    }
                    else
                    {
                        Logger.LogWarning("No valid coordinates found after filtering, using empty array");
                    }
                }
                else
                {
                    Logger.LogInfo("No suggested places found, using empty coordinate array");
                }

                Logger.LogInfo($"Map center coordinates: lat={lat}, lng={lng}");
                Logger.LogInfo($"Coordinate array length: {coordArray.Length}");
                Logger.LogInfo($"Coordinate array content: {coordArray}");

                var finalHtml = htmlTemplate
                    .Replace("{API_KEY}", kakaoMapKey)
                    .Replace("{LAT}", lat.ToString(CultureInfo.InvariantCulture))
                    .Replace("{LNG}", lng.ToString(CultureInfo.InvariantCulture))
                    .Replace("{COORD_ARRAY}", coordArray);

                await MapWebView.EnsureCoreWebView2Async();
                MapWebView.NavigateToString(finalHtml);
            }
            catch (Exception ex)
            {
                Logger.LogError($"Failed to load map: {ex.Message}", ex);
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

        private void ViewLogButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var logContents = Logger.GetLogContents();
                var logWindow = new Window
                {
                    Title = "Curato Debug Log",
                    Width = 800,
                    Height = 600,
                    WindowStartupLocation = WindowStartupLocation.CenterScreen,
                    ResizeMode = ResizeMode.CanResize
                };

                var textBox = new TextBox
                {
                    Text = logContents,
                    IsReadOnly = true,
                    VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                    HorizontalScrollBarVisibility = ScrollBarVisibility.Auto,
                    FontFamily = new System.Windows.Media.FontFamily("Consolas"),
                    FontSize = 12
                };

                var clearButton = new Button
                {
                    Content = "Clear Log",
                    Width = 100,
                    Height = 30,
                    Margin = new Thickness(10),
                    HorizontalAlignment = HorizontalAlignment.Right
                };

                clearButton.Click += (s, args) =>
                {
                    Logger.ClearLog();
                    textBox.Text = "Log cleared.";
                };

                var buttonPanel = new StackPanel
                {
                    Orientation = Orientation.Horizontal,
                    HorizontalAlignment = HorizontalAlignment.Right,
                    Margin = new Thickness(10)
                };
                buttonPanel.Children.Add(clearButton);

                var mainPanel = new DockPanel();
                DockPanel.SetDock(buttonPanel, Dock.Top);
                mainPanel.Children.Add(buttonPanel);
                mainPanel.Children.Add(textBox);

                logWindow.Content = mainPanel;
                logWindow.Show();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to show log: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }
}


