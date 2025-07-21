using System.Windows.Media;
using System.Windows.Controls.Primitives;
using System.Windows.Shapes;
using System.Windows.Media.Animation;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Data;
using Curato.ViewModels;
using Curato;

namespace Curato.Views
{
    public partial class SearchPage : UserControl
    {
        public SearchPage()
        {
            InitializeComponent();
            this.DataContext = new InputViewModel();
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
                    Padding = new Thickness(8)
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
                CategoryGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
                CategoryGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
                CategoryGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            }

            var chipStyle = (Style)FindResource("TimeChipStyle");
            var satoshi = (FontFamily)FindResource("SatoshiMedium");

            // Loop and place each option
            var categories = vm.CategoryOptions;
            for (int i = 0; i < categories.Count; i++)
            {
                string cat = categories[i];
                bool selected = cat == vm.SelectedCategory;

                // text
                var text = new TextBlock
                {
                    Text = cat,
                    FontSize = 24,
                    FontFamily = satoshi,
                    Foreground = Brushes.Black,
                    VerticalAlignment = VerticalAlignment.Center
                };

                var panel = new StackPanel
                {
                    Orientation = Orientation.Horizontal,
                    Children = { text },
                    Margin = new Thickness(0, 5, 0, 0)
                };

                // chip-style button
                var btn = new Button
                {
                    Style = chipStyle,
                    Content = panel,
                    Cursor = Cursors.Hand,
                    Padding = new Thickness(10)
                };
                btn.Click += (_, _) =>
                {
                    vm.SelectedCategory = cat;
                    CategoryPopup.IsOpen = false;
                };

                // place at row/col
                int row = i / 3;
                int col = i % 3;
                Grid.SetRow(btn, row);
                Grid.SetColumn(btn, col);

                CategoryGrid.Children.Add(btn);
            }

            CategoryPopup.IsOpen = true;
        }
        
        private void GenerateButton_Click(object sender, RoutedEventArgs e)
        {
            if (DataContext is InputViewModel vm)
            {
                if (vm.GeneratePlanCommand.CanExecute(null))
                    vm.GeneratePlanCommand.Execute(null);
            }

            var mainWindow = Window.GetWindow(this) as MainWindow;
            if (mainWindow != null)
            {
                // Swap out the current page without using navigation to avoid crashes
                mainWindow.MainFrame.Content = new LoadingPage();
            }
        }
    }
}