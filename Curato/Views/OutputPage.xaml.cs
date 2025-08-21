using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Threading;
using System.Globalization;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using Curato;
using Curato.Models;
using Curato.Views;
using Microsoft.Web.WebView2.Wpf;
using secure;
using Curato.Helpers;
using System.Text;

namespace Curato.Views
{
    public partial class OutputPage : UserControl
    {
        public double Latitude { get; set; } = 37.5665; // default to Seoul
        public double Longitude { get; set; } = 126.9780;
        private readonly StringBuilder _streamingStoryBuilder = new StringBuilder();
        private bool _isStreaming = false;
        private DateTime _streamingStartTime;
        private const int BEGIN_MARKER_TIMEOUT_SECONDS = 30; // 30 seconds timeout for [BEGIN] marker

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
            // Set the DataContext to the shared InputViewModel for proper data binding
            this.DataContext = AppState.SharedInputViewModel;
            
            // Set preferences summary using the ViewModel's property
            if (AppState.SharedInputViewModel != null)
            {
                var vm = AppState.SharedInputViewModel;
                // Use the existing PreferencesSummary property from the ViewModel
                PreferencesSummaryLabel.Text = vm.PreferencesSummary;
            }
            else
            {
                PreferencesSummaryLabel.Text = "Preferences not available";
            }

            // Check if we have a plan from AppState
            var plan = AppState.SharedTripPlan;

            if (plan != null && !string.IsNullOrWhiteSpace(plan.EmotionalNarrative))
            {
                // Clean the content to remove prompt instructions
                var cleanedContent = CleanStoryContent(plan.EmotionalNarrative);
                
                EmotionalItineraryTextBlock.Inlines.Clear();
                foreach (var para in cleanedContent.Split(new[] { "\n", "\r\n" }, StringSplitOptions.RemoveEmptyEntries))
                {
                    EmotionalItineraryTextBlock.Inlines.Clear();
                    EmotionalItineraryTextBlock.Inlines.Add(new Run(para.Trim()));
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                }
            }
            else
            {
                EmotionalItineraryTextBlock.Text = "Story is being generated in real-time...\n\n";
                
                // Try to reload from AppState after a longer delay
                await Task.Delay(1000);
                var retryPlan = AppState.SharedTripPlan;
                if (retryPlan != null && !string.IsNullOrWhiteSpace(retryPlan.EmotionalNarrative))
                {
                    // Clean the content to remove prompt instructions
                    var cleanedRetryContent = CleanStoryContent(retryPlan.EmotionalNarrative);
                    
                    EmotionalItineraryTextBlock.Inlines.Clear();
                    foreach (var para in cleanedRetryContent.Split(new[] { "\n", "\r\n" }, StringSplitOptions.RemoveEmptyEntries))
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
                var htmlTemplate = File.ReadAllText(htmlPath, Encoding.UTF8);
                var kakaoMapKey = crypto_utils.get_kakao_map_api_key();

                // Get the plan from AppState
                var JSplan = AppState.SharedTripPlan ?? new TripPlan();
                
                // Use the actual suggested places from the generated plan
                if (JSplan.SuggestedPlaces != null && JSplan.SuggestedPlaces.Count > 0)
                {
                    // Find the first valid coordinate set
                    var firstValidPlace = JSplan.SuggestedPlaces.FirstOrDefault(p => 
                        p.Latitude != 0 && p.Longitude != 0 && 
                        p.Latitude >= 33.0 && p.Latitude <= 38.5 &&  // Valid Korea latitude range
                        p.Longitude >= 124.0 && p.Longitude <= 132.0 && // Valid Korea longitude range
                        // Filter out fake/placeholder coordinates
                        !(p.Latitude == 37.123456 && p.Longitude == 126.123456) &&
                        !(p.Latitude == 37.0 && p.Longitude == 126.0) &&
                        !(p.Latitude == 0.0 && p.Longitude == 0.0) &&
                        // Filter out generic placeholder names
                        !string.IsNullOrWhiteSpace(p.Name) &&
                        p.Name != "Location Name" &&
                        p.Name != "Full Address" &&
                        p.Name != "Category" &&
                        p.Name != "Distance from start" &&
                        p.Name != "Kakao Map URL"
                    );
                    
                    if (firstValidPlace != null)
                    {
                        // Use the first valid place for map center
                        lat = firstValidPlace.Latitude;
                        lng = firstValidPlace.Longitude;
                    }
                    else
                    {
                        lat = 37.5665; // Seoul
                        lng = 126.9780;
                    }
                }

                string coordArray = "[]"; // Default empty array
                
                if (JSplan.SuggestedPlaces != null && JSplan.SuggestedPlaces.Any())
                {
                    // Filter out invalid coordinates and create the array
                    var validPlaces = JSplan.SuggestedPlaces.Where(p => 
                        p.Latitude != 0 && p.Longitude != 0 && 
                        p.Latitude >= 33.0 && p.Latitude <= 38.5 &&  // Valid Korea latitude range
                        p.Longitude >= 124.0 && p.Longitude <= 132.0 && // Valid Korea longitude range
                        // Filter out fake/placeholder coordinates
                        !(p.Latitude == 37.123456 && p.Longitude == 126.123456) &&
                        !(p.Latitude == 37.0 && p.Longitude == 126.0) &&
                        !(p.Latitude == 0.0 && p.Longitude == 0.0) &&
                        // Filter out generic placeholder names
                        !string.IsNullOrWhiteSpace(p.Name) &&
                        p.Name != "Location Name" &&
                        p.Name != "Full Address" &&
                        p.Name != "Category" &&
                        p.Name != "Distance from start" &&
                        p.Name != "Kakao Map URL"
                    ).ToList();
                    
                    if (validPlaces.Any())
                    {
                        coordArray = "["
                            + string.Join(",", validPlaces
                                .Select((p, i) =>
                                    $"{{ lat: {p.Latitude.ToString(CultureInfo.InvariantCulture)}, lng: {p.Longitude.ToString(CultureInfo.InvariantCulture)}, name: \"{p.Name.Replace("\"", "\\\"")}\", index: {i + 1} }}"))
                            + "]";
                    }
                }

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

        /// <summary>
        /// Cleans the story content by removing prompt instructions and technical markers
        /// </summary>
        /// <param name="rawContent">Raw content from the AI model</param>
        /// <returns>Cleaned content suitable for display</returns>
        private string CleanStoryContent(string rawContent)
        {
            if (string.IsNullOrWhiteSpace(rawContent))
                return rawContent;

            var lines = rawContent.Split(new[] { "\n", "\r\n" }, StringSplitOptions.RemoveEmptyEntries);
            var cleanedLines = new List<string>();

            foreach (var line in lines)
            {
                var trimmedLine = line.Trim();
                
                // Skip lines that contain prompt instructions
                if (trimmedLine.StartsWith("You are a professional travel writer") ||
                    trimmedLine.StartsWith("Create a comprehensive itinerary") ||
                    trimmedLine.StartsWith("IMPORTANT:") ||
                    trimmedLine.StartsWith("Context:") ||
                    trimmedLine.StartsWith("Requirements:") ||
                    trimmedLine.StartsWith("Output Format:") ||
                    trimmedLine.StartsWith("Selected Locations:") ||
                    trimmedLine.StartsWith("I'll create a comprehensive itinerary") ||
                    trimmedLine.StartsWith("I have now covered all") ||
                    trimmedLine.StartsWith("[BEGIN]:") ||
                    trimmedLine.StartsWith("[END]") ||
                    trimmedLine.StartsWith("1.") && trimmedLine.Contains("Place Name") ||
                    trimmedLine.StartsWith("2.") && trimmedLine.Contains("Place Name") ||
                    trimmedLine.StartsWith("3.") && trimmedLine.Contains("Place Name") ||
                    trimmedLine.StartsWith("4.") && trimmedLine.Contains("Place Name") ||
                    trimmedLine.StartsWith("5.") && trimmedLine.Contains("Place Name"))
                {
                    continue; // Skip this line
                }

                // Skip empty lines and technical markers
                if (string.IsNullOrWhiteSpace(trimmedLine) || 
                    trimmedLine.StartsWith("\\") ||
                    trimmedLine.StartsWith("Continue this format"))
                {
                    continue;
                }

                cleanedLines.Add(trimmedLine);
            }

            return string.Join("\n", cleanedLines);
        }

        /// <summary>
        /// Receives streaming tokens for real-time story display with frontend filtering
        /// </summary>
        /// <param name="token">The token to display</param>
        /// <param name="isFinal">Whether this is the final token</param>
        public void ReceiveStreamingToken(string token, bool isFinal = false)
        {
            try
            {
                if (isFinal)
                {
                    // Final token received - story generation complete
                    _isStreaming = false;
                    Logger.LogInfo("Streaming completed - story generation finished");
                    
                    // Log the complete story for debugging
                    var completeStory = _streamingStoryBuilder.ToString();
                    Logger.LogInfo($"Complete story received: {completeStory.Substring(0, Math.Min(200, completeStory.Length))}...");
                    
                    // Clean up any remaining content after [END] marker
                    var cleanedStory = CleanupStoryAfterEnd(completeStory);
                    
                    // Update the final story in AppState if we have a complete story
                    if (!string.IsNullOrWhiteSpace(cleanedStory))
                    {
                        if (AppState.SharedTripPlan != null)
                        {
                            AppState.SharedTripPlan.EmotionalNarrative = cleanedStory;
                        }
                        Logger.LogInfo($"Final cleaned story saved to AppState: {cleanedStory.Substring(0, Math.Min(100, cleanedStory.Length))}...");
                    }
                    return;
                }
                
                if (string.IsNullOrEmpty(token))
                    return;
                
                // Start streaming mode if not already started
                if (!_isStreaming)
                {
                    _isStreaming = true;
                    _streamingStartTime = DateTime.Now;
                    _streamingStoryBuilder.Clear();
                    EmotionalItineraryTextBlock.Inlines.Clear();
                    
                    // Show loading message while waiting for [BEGIN] marker
                    EmotionalItineraryTextBlock.Inlines.Add(new Run("Generating your personalized itinerary..."));
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                    
                    Logger.LogInfo("Starting real-time story streaming with frontend filtering");
                }
                
                // Check for timeout if we haven't found [BEGIN] marker yet
                var fullContent = _streamingStoryBuilder.ToString();
                if (!fullContent.Contains("[BEGIN]: "))
                {
                    var elapsedSeconds = (DateTime.Now - _streamingStartTime).TotalSeconds;
                    if (elapsedSeconds > BEGIN_MARKER_TIMEOUT_SECONDS)
                    {
                        Logger.LogInfo($"Timeout waiting for [BEGIN] marker after {elapsedSeconds:F1} seconds. Showing content anyway.");
                        // Show a warning message
                        Dispatcher.Invoke(() =>
                        {
                            EmotionalItineraryTextBlock.Inlines.Clear();
                            EmotionalItineraryTextBlock.Inlines.Add(new Run("Warning: [BEGIN] marker not found. Displaying all content."));
                            EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                            EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                        });
                    }
                    else if (elapsedSeconds > BEGIN_MARKER_TIMEOUT_SECONDS * 0.8) // Log when approaching timeout
                    {
                        Logger.LogInfo($"Approaching timeout: {elapsedSeconds:F1}s elapsed, timeout at {BEGIN_MARKER_TIMEOUT_SECONDS}s");
                    }
                }
                
                Logger.LogInfo($"Received streaming token: '{token.Substring(0, Math.Min(50, token.Length))}...'");
                
                // Add token to builder for complete story tracking
                _streamingStoryBuilder.Append(token);
                
                // Check for extremely long content and truncate if needed
                var currentContent = _streamingStoryBuilder.ToString();
                if (currentContent.Length > 10000)
                {
                    Logger.LogInfo("Content length exceeds 10,000 characters, truncating");
                    _streamingStoryBuilder.Clear();
                    _streamingStoryBuilder.Append(TruncateLongContent(currentContent));
                }
                
                // Real-time frontend filtering: only show content between [BEGIN] and [END] markers
                var filteredToken = FilterTokenForDisplay(token);
                
                if (!string.IsNullOrEmpty(filteredToken))
                {
                    // Display filtered token in real-time
                    Dispatcher.Invoke(() =>
                    {
                        EmotionalItineraryTextBlock.Inlines.Add(new Run(filteredToken));
                        
                        // Auto-scroll to bottom
                        var scrollViewer = FindScrollViewer();
                        if (scrollViewer != null)
                        {
                            scrollViewer.ScrollToBottom();
                        }
                    });
                    
                    Logger.LogInfo($"Displayed filtered token: {filteredToken.Substring(0, Math.Min(50, filteredToken.Length))}...");
                }
                else
                {
                    Logger.LogInfo($"Filtered out token: {token.Substring(0, Math.Min(50, token.Length))}...");
                }
                
                // Log streaming stats periodically (every 10 tokens or so)
                if (_streamingStoryBuilder.Length % 100 < token.Length)
                {
                    LogStreamingStats();
                }
                
            }
            catch (Exception ex)
            {
                Logger.LogError($"Error processing streaming token: {ex.Message}", ex);
            }
        }
        
        /// <summary>
        /// Filters tokens to only show content between [BEGIN] and [END] markers
        /// </summary>
        /// <param name="token">The raw token to filter</param>
        /// <returns>Filtered token content, or empty string if should not be displayed</returns>
        private string FilterTokenForDisplay(string token)
        {
            // Get the current state from the full content
            var fullContent = _streamingStoryBuilder.ToString();
            var hasBegin = fullContent.Contains("[BEGIN]: ");
            var hasEnd = fullContent.Contains("[END]");
            
            // Log the current state for debugging
            LogCurrentStreamingState(fullContent, hasBegin, hasEnd);
            
            // Validate the streaming state
            ValidateStreamingState(fullContent, hasBegin, hasEnd);
            
            // Handle malformed markers
            if (!HandleMalformedMarkers(fullContent))
            {
                Logger.LogInfo("Malformed markers detected, proceeding with caution");
            }
            
            Logger.LogInfo($"Filtering token: hasBegin={hasBegin}, hasEnd={hasEnd}, token='{token.Substring(0, Math.Min(30, token.Length))}...'");
            
            // Check if this token contains the [BEGIN] marker
            if (token.Contains("[BEGIN]"))
            {
                Logger.LogInfo("Found [BEGIN] marker in token");
                
                // Clear the loading message when we find [BEGIN]
                ClearLoadingMessage();
                
                // Extract content after [BEGIN] marker
                var beginIndex = token.IndexOf("[BEGIN]: ");
                var contentAfterBegin = token.Substring(beginIndex + "[BEGIN]: ".Length);
                
                // Only show content after [BEGIN] if it's not empty
                if (!string.IsNullOrWhiteSpace(contentAfterBegin))
                {
                    Logger.LogInfo($"Returning content after [BEGIN]: '{contentAfterBegin.Substring(0, Math.Min(30, contentAfterBegin.Length))}...'");
                    return contentAfterBegin;
                }
                Logger.LogInfo("No content after [BEGIN] marker");
                return string.Empty;
            }
            
            // Check if this token contains the [END] marker
            if (token.Contains("[END]"))
            {
                Logger.LogInfo("Found [END] marker in token");
                // Extract content before [END] marker
                var endIndex = token.IndexOf("[END] ");
                if (endIndex > 0)
                {
                    var contentBeforeEnd = token.Substring(0, endIndex);
                    Logger.LogInfo($"Returning content before [END]: '{contentBeforeEnd.Substring(0, Math.Min(30, contentBeforeEnd.Length))}...'");
                    return contentBeforeEnd;
                }
                Logger.LogInfo("No content before [END] marker");
                return string.Empty;
            }
            
            // Handle edge case: check if this token completes a partial [BEGIN] marker
            if (!hasBegin && !hasEnd)
            {
                var partialBegin = fullContent.EndsWith("[") && token.StartsWith("BEGIN]");
                if (partialBegin)
                {
                    Logger.LogInfo("Found partial [BEGIN] marker completion");
                    var contentAfterBegin = token.Substring("BEGIN]: ".Length);
                    if (!string.IsNullOrWhiteSpace(contentAfterBegin))
                    {
                        Logger.LogInfo($"Returning content after completed [BEGIN]: '{contentAfterBegin.Substring(0, Math.Min(30, contentAfterBegin.Length))}...'");
                        return contentAfterBegin;
                    }
                    return string.Empty;
                }
                
                var partialEnd = fullContent.EndsWith("[") && token.StartsWith("END]");
                if (partialEnd)
                {
                    Logger.LogInfo("Found partial [END] marker completion");
                    return string.Empty;
                }
            }
            
            // If we're between [BEGIN] and [END], show the token
            if (hasBegin && !hasEnd)
            {
                // We're between [BEGIN] and [END] - show this token
                Logger.LogInfo("Token is between [BEGIN] and [END] - displaying");
                return token;
            }
            
            // Handle timeout case: if we've been waiting too long, show content anyway
            if (!hasBegin)
            {
                var elapsedSeconds = (DateTime.Now - _streamingStartTime).TotalSeconds;
                if (elapsedSeconds > BEGIN_MARKER_TIMEOUT_SECONDS)
                {
                    Logger.LogInfo($"Timeout reached, showing token despite missing [BEGIN] marker");
                    return token;
                }
            }
            
            // We're either before [BEGIN] or after [END] - don't show
            Logger.LogInfo($"Token filtered out: before [BEGIN]={!hasBegin}, after [END]={hasEnd}");
            return string.Empty;
        }
        
        /// <summary>
        /// Clears the loading message when [BEGIN] marker is found
        /// </summary>
        private void ClearLoadingMessage()
        {
            Dispatcher.Invoke(() =>
            {
                EmotionalItineraryTextBlock.Inlines.Clear();
                Logger.LogInfo("Cleared loading message, ready to display story content");
            });
        }
        
        /// <summary>
        /// Cleans up the story by removing content after [END] marker
        /// </summary>
        /// <param name="completeStory">The complete story with all markers</param>
        /// <returns>Cleaned story content</returns>
        private string CleanupStoryAfterEnd(string completeStory)
        {
            var endIndex = completeStory.IndexOf("[END]");
            if (endIndex >= 0)
            {
                var cleanedStory = completeStory.Substring(0, endIndex);
                Logger.LogInfo($"Cleaned story after [END] marker. Original length: {completeStory.Length}, Cleaned length: {cleanedStory.Length}");
                return cleanedStory;
            }
            
            Logger.LogInfo("No [END] marker found in complete story, returning as-is");
            return completeStory;
        }
        
        /// <summary>
        /// Logs streaming statistics for performance monitoring
        /// </summary>
        private void LogStreamingStats()
        {
            if (_isStreaming)
            {
                var elapsed = DateTime.Now - _streamingStartTime;
                var contentLength = _streamingStoryBuilder.Length;
                var hasBegin = _streamingStoryBuilder.ToString().Contains("[BEGIN]: ");
                var hasEnd = _streamingStoryBuilder.ToString().Contains("[END]");
                
                Logger.LogInfo($"Streaming Stats - Elapsed: {elapsed.TotalSeconds:F1}s, Content: {contentLength} chars, [BEGIN]: {hasBegin}, [END]: {hasEnd}");
            }
        }
        
        /// <summary>
        /// Truncates extremely long content to prevent memory issues
        /// </summary>
        /// <param name="content">The content to check</param>
        /// <param name="maxLength">Maximum allowed length</param>
        /// <returns>Truncated content if needed</returns>
        private string TruncateLongContent(string content, int maxLength = 10000)
        {
            if (content.Length > maxLength)
            {
                Logger.LogInfo($"Content length ({content.Length}) exceeds maximum ({maxLength}), truncating");
                return content.Substring(0, maxLength) + "... [TRUNCATED]";
            }
            return content;
        }
        
        /// <summary>
        /// Handles malformed or partial markers
        /// </summary>
        /// <param name="fullContent">The complete content received so far</param>
        /// <returns>True if markers are properly formed, false otherwise</returns>
        private bool HandleMalformedMarkers(string fullContent)
        {
            // Check for partial markers that might cause issues
            var partialBegin = fullContent.Contains("[") && !fullContent.Contains("[BEGIN]");
            var partialEnd = fullContent.Contains("[") && !fullContent.Contains("[END]");
            
            if (partialBegin || partialEnd)
            {
                Logger.LogInfo($"Found partial markers: partialBegin={partialBegin}, partialEnd={partialEnd}");
                return false;
            }
            
            return true;
        }
        
        /// <summary>
        /// Checks if the streaming state is valid and logs any issues
        /// </summary>
        /// <param name="fullContent">The complete content received so far</param>
        /// <param name="hasBegin">Whether [BEGIN] marker has been found</param>
        /// <param name="hasEnd">Whether [END] marker has been found</param>
        private void ValidateStreamingState(string fullContent, bool hasBegin, bool hasEnd)
        {
            // Check for potential issues
            if (hasEnd && !hasBegin)
            {
                Logger.LogInfo("Found [END] marker without [BEGIN] marker - this shouldn't happen");
            }
            
            if (fullContent.Contains("[BEGIN]: ") && fullContent.Contains("[END]"))
            {
                var beginIndex = fullContent.IndexOf("[BEGIN]: ");
                var endIndex = fullContent.IndexOf("[END]");
                if (endIndex < beginIndex)
                {
                    Logger.LogInfo("[END] marker appears before [BEGIN] marker - this shouldn't happen");
                }
            }
        }
        
        /// <summary>
        /// Logs the current streaming state for debugging
        /// </summary>
        /// <param name="fullContent">The complete content received so far</param>
        /// <param name="hasBegin">Whether [BEGIN] marker has been found</param>
        /// <param name="hasEnd">Whether [END] marker has been found</param>
        private void LogCurrentStreamingState(string fullContent, bool hasBegin, bool hasEnd)
        {
            var contentLength = fullContent.Length;
            var beginIndex = fullContent.IndexOf("[BEGIN]: ");
            var endIndex = fullContent.IndexOf("[END]");
            
            Logger.LogInfo($"Streaming State - Content Length: {contentLength}, [BEGIN] at: {beginIndex}, [END] at: {endIndex}");
            
            if (beginIndex >= 0)
            {
                var beforeBegin = fullContent.Substring(0, beginIndex);
                Logger.LogInfo($"Content before [BEGIN]: '{beforeBegin.Substring(0, Math.Min(50, beforeBegin.Length))}...'");
            }
            
            if (endIndex >= 0 && beginIndex >= 0)
            {
                var betweenMarkers = fullContent.Substring(beginIndex + "[BEGIN]".Length, endIndex - beginIndex - "[BEGIN]".Length);
                Logger.LogInfo($"Content between markers: '{betweenMarkers.Substring(0, Math.Min(100, betweenMarkers.Length))}...'");
            }
        }
        
        /// <summary>
        /// Finds the ScrollViewer parent of the EmotionalItineraryTextBlock
        /// </summary>
        private ScrollViewer? FindScrollViewer()
        {
            var parent = EmotionalItineraryTextBlock.Parent as FrameworkElement;
            while (parent != null)
            {
                if (parent is ScrollViewer scrollViewer)
                    return scrollViewer;
                parent = parent.Parent as FrameworkElement;
            }
            return null;
        }
    }
}