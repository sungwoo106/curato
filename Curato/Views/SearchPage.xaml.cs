using System.Windows.Media;
using System.Windows.Controls.Primitives;
using System.Windows.Shapes;
using System.Windows.Media.Animation;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
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

            var popup = new ContextMenu
            {
                Style = (Style)FindResource("AnimatedContextMenuStyle"),
                Background = Brushes.White,
                BorderThickness = new Thickness(0),
                Placement = PlacementMode.Bottom,
                PlacementTarget = sender as UIElement,
                Padding = new Thickness(8),
                MaxHeight = 240,
                MinWidth = 190,
                HasDropShadow = true,
                Opacity = 0 // ensure the animation starts from 0
            };

            foreach (string type in vm.CompanionTypes)
            {
                var isSelected = type == vm.SelectedCompanion;

                var container = new Border
                {
                    Background = Brushes.White,
                    CornerRadius = new CornerRadius(50),
                    Padding = new Thickness(12, 8, 12, 8),
                    Margin = new Thickness(4)
                };

                var dot = new Ellipse
                {
                    Width = 25,
                    Height = 25,
                    Fill = isSelected
                        ? new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FFB31A"))
                        : Brushes.LightGray,
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

                var stack = new StackPanel
                {
                    Orientation = Orientation.Horizontal,
                    Children = { dot, text }
                };

                container.Child = stack;

                var item = new MenuItem
                {
                    Header = container,
                    Background = Brushes.Transparent,
                    BorderThickness = new Thickness(0),
                    Padding = new Thickness(0)
                };

                item.Click += (_, _) => vm.SelectedCompanion = type;

                popup.Items.Add(item);
            }

            popup.IsOpen = true;
        }

    }
}