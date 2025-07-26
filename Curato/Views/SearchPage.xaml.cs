using System.IO;
using System.Windows.Media;
using System.Windows.Controls.Primitives;
using System.Windows.Shapes;
using System.Windows.Media.Animation;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Data;
using System.Windows.Threading;
using System.Threading.Tasks;
using Curato.ViewModels;
using Curato.Models;
using Curato;

namespace Curato.Views
{
    public partial class SearchPage : UserControl
    {
        private readonly DispatcherTimer _locationTimer = new DispatcherTimer();

        public SearchPage()
        {
            InitializeComponent();
            var vm = AppState.SharedInputViewModel;
            this.DataContext = vm;
            LocationSuggestionPopup.DataContext = vm;
            // Setup debounced search logic in the code-behind to call a Python helper script and populate suggestions asynchronously
            _locationTimer.Interval = TimeSpan.FromMilliseconds(500);
            _locationTimer.Tick += LocationTimer_Tick;

            // Debug: Track what UI element receives the MouseLeftButtonUp event
            EventManager.RegisterClassHandler(typeof(Border),
                UIElement.MouseLeftButtonUpEvent,
                new MouseButtonEventHandler((s, e) =>
                {
                    string path = System.IO.Path.Combine(AppContext.BaseDirectory, "event_trace.txt");
                    File.AppendAllText(path, $"[Border] Click on: {s.GetType().Name}, Tag={((s as FrameworkElement)?.Tag ?? "null")}\n");
                }));
        }

        private void LocationTextBox_TextChanged(object sender, TextChangedEventArgs e)
        {
            _locationTimer.Stop();
            _locationTimer.Start();
        }

        private void LocationTextBox_GotFocus(object sender, RoutedEventArgs e)
        {
            if (DataContext is InputViewModel vm && vm.LocationQuery == "Search Location")
            {
                vm.LocationQuery = string.Empty;
            }
        }

        private async void LocationTimer_Tick(object? sender, EventArgs e)
        {
            _locationTimer.Stop();
            if (DataContext is not InputViewModel vm)
                return;

            string query = vm.LocationQuery;

            if (string.IsNullOrWhiteSpace(query))
            {
                vm.LocationSuggestions.Clear();
                vm.IsLocationPopupOpen = false;
                return;
            }

            try
            {
                var scriptPath = System.IO.Path.GetFullPath(System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, @"..\..\..\..\core\location_suggest.py"));

                var psi = new ProcessStartInfo
                {
                    // Change this to your Python executable path
                    FileName = @"C:\Users\sungw\AppData\Local\Programs\Python\Python310\python.exe",
                    Arguments = $"\"{scriptPath}\" \"{query}\"",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true, // capture error
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var process = Process.Start(psi);
                using var reader = new StreamReader(process.StandardOutput.BaseStream, Encoding.UTF8);
                string result = await reader.ReadToEndAsync();
                
                await process.WaitForExitAsync();

                var suggestions = JsonSerializer.Deserialize<List<PlaceSuggestion>>(result);
                vm.LocationSuggestions = new ObservableCollection<PlaceSuggestion>(suggestions ?? new());

                vm.IsLocationPopupOpen = vm.LocationSuggestions.Count > 0;

            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error fetching location suggestions: {ex.Message}");
                vm.LocationSuggestions = new();
                vm.IsLocationPopupOpen = false;
            }

        }
        
        private void Suggestion_Click(object sender, MouseButtonEventArgs e)
        {
            if (sender is TextBlock tb && tb.DataContext is PlaceSuggestion suggestion)
            {
                if (DataContext is InputViewModel vm)
                {
                    vm.LocationQuery = suggestion.Name;
                    vm.SelectedLocationCoordinates = (suggestion.Latitude, suggestion.Longitude);
                    vm.IsLocationPopupOpen = false;
                }
            }
        }


        private void CompanionButton_Click(object sender, RoutedEventArgs e)
        {
            if (DataContext is not InputViewModel vm)
                return;

            CompanionItemsControl.Items.Clear();

            foreach (string type in vm.CompanionTypes)
            {
                var isSelected = type == vm.SelectedCompanion;

                var dot = new Ellipse
                {
                    Width = 25,
                    Height = 25,
                    Fill = isSelected ? new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FFB31A")) : Brushes.LightGray,
                    VerticalAlignment = VerticalAlignment.Center,
                    Margin = new Thickness(0, 0, 10, 0)
                };

                var text = new TextBlock
                {
                    Text = type,
                    FontSize = 24,
                    Foreground = Brushes.Black,
                    VerticalAlignment = VerticalAlignment.Center,
                    FontFamily = new FontFamily("{StaticResource SatoshiMedium}")
                };

                var panel = new StackPanel
                {
                    Orientation = Orientation.Horizontal,
                    Children = { dot, text },
                    Margin = new Thickness(0, 5, 0, 0)
                };

                var container = new Border
                {
                    CornerRadius = new CornerRadius(8),
                    Background = Brushes.Transparent,
                    Child = panel,
                    Cursor = Cursors.Hand,
                    Padding = new Thickness(10, 10, 10, 10)
                };

                container.MouseLeftButtonUp += (_, _) =>
                {
                    vm.SelectedCompanion = type;
                    CompanionPopup.IsOpen = false;
                };

                CompanionItemsControl.Items.Add(container);
            }

            CompanionPopup.IsOpen = true;
        }

        private void BudgetButton_Click(object sender, RoutedEventArgs e)
        {
            if (DataContext is not InputViewModel vm)
                return;

            BudgetItemsControl.Items.Clear();

            foreach (var option in vm.BudgetOptions)
            {
                bool isSelected = option == vm.SelectedBudget;

                // yellow dot same as Companion
                var dot = new Ellipse
                {
                    Width = 25,
                    Height = 25,
                    Fill = isSelected
                            ? (Brush)new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FFB31A"))
                            : Brushes.LightGray,
                    VerticalAlignment = VerticalAlignment.Center,
                    Margin = new Thickness(0, 0, 10, 0)
                };

                var text = new TextBlock
                {
                    Text = option,
                    FontSize = 24,
                    Foreground = Brushes.Black,
                    VerticalAlignment = VerticalAlignment.Center,
                    FontFamily = new FontFamily("{StaticResource SatoshiMedium}")
                };

                var panel = new StackPanel
                {
                    Orientation = Orientation.Horizontal,
                    Children = { dot, text },
                    Margin = new Thickness(0, 5, 0, 0)
                };

                var container = new Border
                {
                    CornerRadius = new CornerRadius(8),
                    Background = Brushes.Transparent,
                    Child = panel,
                    Cursor = Cursors.Hand,
                    Padding = new Thickness(10, 10, 10, 10)
                };

                container.MouseLeftButtonUp += (_, _) =>
                {
                    vm.SelectedBudget = option;
                    BudgetPopup.IsOpen = false;
                };

                BudgetItemsControl.Items.Add(container);
            }

            BudgetPopup.IsOpen = true;
        }

        private Popup? _activeTimeSubPopup;
        private void TimeButton_Click(object sender, RoutedEventArgs e)
        {
            if (DataContext is not InputViewModel vm)
                return;

            // Toggle off if already open
            if (TimePopup.IsOpen)
            {
                TimePopup.IsOpen = false;
                if (_activeTimeSubPopup != null)
                {
                    _activeTimeSubPopup.IsOpen = false;
                }
                return;
            }

            // Clear out the containers so we can rebuild
            TimeMainItemsControl.Items.Clear();

            // Build main-period buttons
            foreach (var period in vm.TimeMainOptions)
            {
                bool isMainSelected = period == vm.SelectedMainTime;

                var txt = new TextBlock
                {
                    Text = period,
                    FontSize = 24,
                    VerticalAlignment = VerticalAlignment.Center,
                    FontFamily = new FontFamily("{StaticResource SatoshiMedium}")
                };
                var panel = new StackPanel
                {
                    Orientation = Orientation.Horizontal,
                    Children = { txt },
                    Margin = new Thickness(0, 0, 15, 0)
                };
                var btn = new Button
                {
                    Style = BuildPeriodButtonStyle(period),
                    Content = panel,
                    Cursor = Cursors.Hand,
                    Padding = new Thickness(8),
                    Height = 67
                };

                btn.Click += (_, _) =>
                {
                    vm.SelectedMainTime = period;
                    ShowPeriodOptions(btn, vm.TimeOptionsMap[period]);
                };

                TimeMainItemsControl.Items.Add(btn);

            }

            // Show the main popup
            TimePopup.IsOpen = true;
        }

        private Style BuildPeriodButtonStyle(string period)
        {
            // Base style
            var style = new Style(typeof(Button));

            // Default look
            style.Setters.Add(new Setter(Control.BackgroundProperty, Brushes.White));
            style.Setters.Add(new Setter(Control.ForegroundProperty, Brushes.Black));
            style.Setters.Add(new Setter(Control.PaddingProperty, new Thickness(8)));
            style.Setters.Add(new Setter(Control.FontSizeProperty, 24.0));
            style.Setters.Add(new Setter(Control.FontFamilyProperty, new FontFamily("{StaticResource SatoshiMedium}")));
            style.Setters.Add(new Setter(Control.CursorProperty, Cursors.Hand));

            // 1b) Rounded-corner template
            var template = new ControlTemplate(typeof(Button));
            var borderFactory = new FrameworkElementFactory(typeof(Border));
            borderFactory.SetValue(Border.BackgroundProperty,
                new TemplateBindingExtension(Button.BackgroundProperty));
            borderFactory.SetValue(Border.CornerRadiusProperty, new CornerRadius(20));
            borderFactory.SetValue(Border.PaddingProperty,
                new TemplateBindingExtension(Button.PaddingProperty));
            var contentFactory = new FrameworkElementFactory(typeof(ContentPresenter));
            contentFactory.SetValue(ContentPresenter.HorizontalAlignmentProperty, HorizontalAlignment.Center);
            contentFactory.SetValue(ContentPresenter.VerticalAlignmentProperty, VerticalAlignment.Center);
            borderFactory.AppendChild(contentFactory);
            template.VisualTree = borderFactory;
            style.Setters.Add(new Setter(Button.TemplateProperty, template));

            // 2) Hover & pressed feedback (exact same as your other dropdowns)
            var hoverTrigger = new Trigger { Property = UIElement.IsMouseOverProperty, Value = true };
            hoverTrigger.Setters.Add(new Setter(Control.BackgroundProperty,
                new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FFF2CC"))));
            style.Triggers.Add(hoverTrigger);

            var pressedTrigger = new Trigger { Property = Button.IsPressedProperty, Value = true };
            pressedTrigger.Setters.Add(new Setter(Control.BackgroundProperty,
                new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FFD699"))));
            style.Triggers.Add(pressedTrigger);

            // 3) DataTrigger: when this button's period == vm.SelectedMainTime, accent it
            var selectedTrigger = new DataTrigger
            {
                Binding = new Binding(nameof(InputViewModel.SelectedMainTime))
                {
                    Source = this.DataContext
                },
                Value = period
            };
            selectedTrigger.Setters.Add(new Setter(Control.BackgroundProperty,
                new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FFB31A"))));
            selectedTrigger.Setters.Add(new Setter(Control.ForegroundProperty, Brushes.White));
            style.Triggers.Add(selectedTrigger);

            return style;
        }

        private void ShowPeriodOptions(Button target, List<string> options)
        {
            if (DataContext is not InputViewModel vm) return;

            // Close any previously opened sub popup to avoid crashes
            if (_activeTimeSubPopup != null)
            {
                _activeTimeSubPopup.IsOpen = false;
            }

            // Build the Popup
            var popup = new Popup
            {
                PlacementTarget = target,
                Placement = PlacementMode.Bottom,
                StaysOpen = false,
                AllowsTransparency = true,
                PopupAnimation = PopupAnimation.Slide,
                MaxHeight = 300,
                Width = 204,
                VerticalOffset = 40 // Adjusted for better visibility
            };

            // Container border
            var border = new Border
            {
                Background = Brushes.White,
                CornerRadius = new CornerRadius(30),
                Padding = new Thickness(10),
                BorderBrush = (Brush)new SolidColorBrush((Color)ColorConverter.ConvertFromString("#DDD")),
                BorderThickness = new Thickness(1)
            };

            // Vertical stack for each slot
            var stack = new StackPanel
            {
                Orientation = Orientation.Vertical
            };

            foreach (var slot in options)
            {
                bool isSelected = slot == vm.SelectedSubTime;

                var dot = new Ellipse
                {
                    Width = 25,
                    Height = 25,
                    Fill = isSelected
                        ? (Brush)new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FFB31A"))
                        : Brushes.LightGray,
                    Margin = new Thickness(0, 0, 6, 0),
                    VerticalAlignment = VerticalAlignment.Center
                };

                var text = new TextBlock
                {
                    Text = slot,
                    FontSize = 20,
                    VerticalAlignment = VerticalAlignment.Center,
                    Foreground = Brushes.Black,
                    FontFamily = new FontFamily("{StaticResource SatoshiMedium}")
                };

                var panel = new StackPanel
                {
                    Orientation = Orientation.Horizontal,
                    Children = { dot, text },
                    Margin = new Thickness(0, 5, 0, 0)
                };

                var container = new Border
                {
                    CornerRadius = new CornerRadius(8),
                    Background = Brushes.Transparent,
                    Child = panel,
                    Cursor = Cursors.Hand,
                    Padding = new Thickness(10, 10, 10, 10)
                };

                container.MouseLeftButtonUp += (_, _) =>
                {
                    vm.SelectedSubTime = slot;
                    // Close the popup after selection
                    popup.IsOpen = false;
                    // also close the main TimePopup
                    this.TimePopup.IsOpen = false;
                };

                stack.Children.Add(container);
            }

            var scroll = new ScrollViewer
            {
                Content = stack,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled,
                MaxHeight = 300
            };

            border.Child = scroll;
            popup.Child = border;
            popup.Closed += (_, _) =>
            {
                if (_activeTimeSubPopup == popup)
                {
                    _activeTimeSubPopup = null;
                }
            };

            _activeTimeSubPopup = popup;
            popup.IsOpen = true;
        }

        private void CategoryButton_Click(object sender, RoutedEventArgs e)
        {
            if (DataContext is not InputViewModel vm) return;

            // Clear old items
            CategoryGrid.Children.Clear();

            // Ensure exactly 2 rows & 3 columns (Auto-sized)
            if (CategoryGrid.RowDefinitions.Count == 0)
            {
                CategoryGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
                CategoryGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
                for (int i = 0; i < 3; i++)
                    CategoryGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            }

            var chipStyle = (Style)FindResource("CategoryChipStyle");
            var satoshi   = (FontFamily)FindResource("SatoshiMedium");

            // Loop and place each option

            for (int i = 0; i < vm.CategoryOptions.Count; i++)
            {
                string cat = vm.CategoryOptions[i];
                bool isSelected = vm.SelectedCategories.Contains(cat);

                // Build text panel
                var tb = new TextBlock
                {
                    Text              = cat,
                    FontSize          = 20,
                    FontFamily        = satoshi,
                    Foreground        = Brushes.Black,
                    VerticalAlignment = VerticalAlignment.Center
                };
                var panel = new StackPanel
                {
                    Orientation = Orientation.Horizontal,
                    Children    = { tb }
                };

                // Create a Button with Chip style
                var btn = new Button
                {
                    Style   = chipStyle,
                    Content = panel,
                    Padding = new Thickness(24, 6, 24, 6),
                    Margin = new Thickness(12, 8, 12, 8),
                    Cursor  = Cursors.Hand,
                    // center it in its star‐sized cell:
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment   = VerticalAlignment.Center
                };

                // If it’s the selected category, tint it
                if (isSelected)
                {
                    btn.Background = (Brush)new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FFB31A"));
                    btn.Foreground = Brushes.White;
                }

                btn.Click += (_, _) =>
                {
                    if (vm.SelectedCategories.Contains(cat))
                    {
                        vm.SelectedCategories.Remove(cat);
                        btn.Background = Brushes.White;
                        btn.Foreground = Brushes.Black;
                    }
                    else
                    {
                        vm.SelectedCategories.Add(cat);
                        btn.Background = (Brush)new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FFB31A"));
                        btn.Foreground = Brushes.White;
                    }
                };

                // position in 2×3 grid
                Grid.SetRow(btn, i / 3);
                Grid.SetColumn(btn, i % 3);

                CategoryGrid.Children.Add(btn);
            }

            CategoryPopup.IsOpen = true;
        }

        private void PopularPlace_Click(object sender, MouseButtonEventArgs e)
        {
            // debugging
            string path = System.IO.Path.Combine(AppContext.BaseDirectory, "popular_click_debug.txt");

            try
            {
                if (sender is FrameworkElement fe)
                {
                    var data = fe.DataContext as PopularPlace;
                    var dcType = data?.GetType().Name ?? "null";
                    var title = data?.Title ?? "[no title]";

                    // Log everything
                    File.AppendAllText(path, $"[Click] Sender={fe.GetType().Name}, Title={title}, DataContext={dcType}\n");

                    if (DataContext is InputViewModel vm)
                    {
                        if (title.Contains("Seongsu", StringComparison.OrdinalIgnoreCase))
                            vm.LocationQuery = "Seongsu";
                        else if (title.Contains("Hongdae", StringComparison.OrdinalIgnoreCase))
                            vm.LocationQuery = "Hongdae";
                        else if (title.Contains("Gangnam", StringComparison.OrdinalIgnoreCase))
                            vm.LocationQuery = "Gangnam";
                        else if (title.Contains("Itaewon", StringComparison.OrdinalIgnoreCase))
                            vm.LocationQuery = "Itaewon";
                        else if (title.Contains("Bukchon", StringComparison.OrdinalIgnoreCase))
                            vm.LocationQuery = "Bukchon";

                        // Restart popup
                        _locationTimer.Stop();
                        _locationTimer.Start();
                    }
                }
            }
            catch (Exception ex)
            {
                File.AppendAllText(path, $"[Exception] {ex.Message}\n");
            }
        }
        
        private async void GenerateButton_Click(object sender, RoutedEventArgs e)
        {
            if (DataContext is not InputViewModel vm)
                return;

            var request = new TripRequest
            {
                Location = vm.LocationQuery,
                Companion = vm.SelectedCompanion,
                Budget = vm.SelectedBudget,
                StartTime = vm.SelectedTime,
                PreferredPlaceTypes = vm.SelectedCategories.ToList(),
            };

            var tripPlan = await PlannerEngine.GenerateTripPlan(request);
            AppState.SharedTripPlan = tripPlan;

            if (mainWindow != null)
            {
                // Save coordinates from ViewModel
                var (lat, lng) = vm.SelectedLocationCoordinates;

                // Create and configure OutputPage
                var outputPage = new OutputPage
                {
                    Latitude = lat,
                    Longitude = lng
                };

                mainWindow.MainFrame.Content = new LoadingPage(() =>
                {
                    return new OutputPage
                    {
                        Latitude = lat,
                        Longitude = lng
                    };
                });
            }
        }
    }
}