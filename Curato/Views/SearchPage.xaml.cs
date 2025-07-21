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

        private void TimeButton_Click(object sender, RoutedEventArgs e)
        {
            if (DataContext is not InputViewModel vm)
                return;

            // Toggle off if already open
            if (TimePopup.IsOpen)
            {
                TimePopup.IsOpen = false;
                return;
            }
            
            // Clear out the containers so we can rebuild
            TimeMainItemsControl.Items.Clear();
            TimeSubItemsControl.Items.Clear();


            // Show the sub-scroll area only if the user has already picked a period
            TimeSubScroll.Visibility = vm.SelectedMainTime != null
                ? Visibility.Visible
                : Visibility.Collapsed;


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

            // If they’d already chosen a period before, re-populate its sub-popup now
            if (vm.SelectedMainTime is not null)
                ShowPeriodOptions(btn, vm.TimeOptionsMap[vm.SelectedMainTime]);

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
            contentFactory.SetValue(ContentPresenter.VerticalAlignmentProperty,   VerticalAlignment.Center);
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

            // 1) Build the Popup
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

            // 2) Container border
            var border = new Border
            {
                Background      = Brushes.White,
                CornerRadius    = new CornerRadius(30),
                Padding         = new Thickness(10),
                BorderBrush     = (Brush)new SolidColorBrush((Color)ColorConverter.ConvertFromString("#DDD")),
                BorderThickness = new Thickness(1)
            };

            // 3) Vertical stack for each slot
            var stack = new StackPanel
            {
                Orientation = Orientation.Vertical
            };

            foreach (var slot in options)
            {
                bool isSelected = slot == vm.SelectedSubTime;

                // dot + text
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
                    // **also close the main TimePopup**
                    this.TimePopup.IsOpen = false;
                };
                stack.Children.Add(container);

                var scroll = new ScrollViewer
                {
                    Content                       = stack,
                    VerticalScrollBarVisibility   = ScrollBarVisibility.Auto,
                    HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled,
                    MaxHeight                     = 300
                };
            }

            border.Child = stack;
            popup.Child  = border;
            popup.IsOpen = true;
        }

    }
}