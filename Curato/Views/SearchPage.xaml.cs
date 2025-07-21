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

            // Clear prior items
            TimeMainItemsControl.Items.Clear();
            TimeSubItemsControl.Items.Clear();
            TimeSubScroll.Visibility = Visibility.Collapsed;
            vm.SelectedMainTime = null;
            vm.SelectedSubTime = null;

            // Grab the style you defined in XAML on your TimeButton
            var chipStyle = this.TimeButton.Style;

            // Reset the popup
            TimePopup.HorizontalOffset = 0;
            TimePopup.VerticalOffset = 0;

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
                    Style   = BuildPeriodButtonStyle(period),
                    Content = panel,
                    Cursor  = Cursors.Hand,
                    Padding = new Thickness(8)
                };

                btn.Click += (_, _) =>
                {
                    vm.SelectedMainTime = period;
                    PopulateSubSlots(vm);
                };

                TimeMainItemsControl.Items.Add(btn);
            }

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
            style.Setters.Add(new Setter(Control.FontSizeProperty, 20.0));
            style.Setters.Add(new Setter(Control.FontFamilyProperty, new FontFamily("{StaticResource SatoshiMedium}")));
            style.Setters.Add(new Setter(Control.CursorProperty, Cursors.Hand));

            // 1b) Rounded-corner template
            var template = new ControlTemplate(typeof(Button));
            var borderFactory = new FrameworkElementFactory(typeof(Border));
            borderFactory.SetValue(Border.BackgroundProperty,
                new TemplateBindingExtension(Button.BackgroundProperty));
            borderFactory.SetValue(Border.CornerRadiusProperty, new CornerRadius(8));
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

        private void PopulateSubSlots(InputViewModel vm)
        {
            TimeSubItemsControl.Items.Clear();
            TimeSubScroll.Visibility = Visibility.Visible;

            // build each sub-slot
            foreach (var slot in vm.TimeOptionsMap[vm.SelectedMainTime!])
            {
                bool isSubSelected = slot == vm.SelectedSubTime;

                var dot = new Ellipse
                {
                    Width = 25,
                    Height = 25,
                    Fill = isSubSelected
                        ? (Brush)new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FFB31A"))
                        : Brushes.LightGray,
                    Margin = new Thickness(0, 0, 10, 0),
                    VerticalAlignment = VerticalAlignment.Center
                };
                var txt = new TextBlock
                {
                    Text = slot,
                    FontSize = 24,
                    VerticalAlignment = VerticalAlignment.Center,
                    FontFamily = new FontFamily("{StaticResource SatoshiMedium}")
                };
                var panel = new StackPanel
                {
                    Orientation = Orientation.Vertical,
                    Children = { dot, txt },
                    Margin = new Thickness(0, 0, 15, 0)
                };
                var btn = new Button
                {
                    Style = (Style)FindResource("TimeChipStyle"),
                    Content = panel,
                    Cursor = Cursors.Hand,
                    Padding = new Thickness(8)
                };
                btn.Click += (_, _) =>
                {
                    vm.SelectedSubTime = slot;
                    TimeSubScroll.Visibility = Visibility.Collapsed;
                    TimePopup.IsOpen = false;
                };

                TimeSubItemsControl.Items.Add(btn);
            }
        }

    }
}